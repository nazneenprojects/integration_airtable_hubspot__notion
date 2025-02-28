# hubspot.py
import asyncio
import base64
import hashlib
import json
import secrets

import httpx
import requests
from dotenv import load_dotenv
import os

from fastapi import Request, HTTPException
from redis_client.redis_client import (
    add_key_value_redis,
    get_value_redis,
    delete_key_redis,
)
from starlette.responses import HTMLResponse

from integrations.integration_item.integration_item import IntegrationItem

# Load the .env file vars
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
authorization_url = os.getenv("AUTHORIZATION_URL")
token_url = os.getenv("TOKEN_URL")
contacts_url = os.getenv("CONTACTS_URL")
account_info_url = os.getenv("ACCOUNT_DETAILS_URL")


# Send user request to Authorization page. This forwards request to Oauth server
# Auth server responds with temporary auth code
async def authorize_hubspot(user_id, org_id):
    """

    :param user_id:
    :param org_id:
    :return:
    """
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = base64.urlsafe_b64encode(
        json.dumps(state_data).encode("utf-8")
    ).decode("utf-8")

    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode("utf-8"))

    auth_url = f"{authorization_url}&state={encoded_state}"
    await asyncio.gather(
        add_key_value_redis(
            f"hubspot_state:{org_id}:{user_id}", json.dumps(state_data), expire=600
        ),
        add_key_value_redis(
            f"hubspot_verifier:{org_id}:{user_id}", code_verifier, expire=600
        ),
    )

    return auth_url


# Exchange temporary auth code for token
async def oauth2callback_hubspot(request: Request):
    """

    :param request:
    :return:
    """
    if request.query_params.get("error"):
        raise HTTPException(
            status_code=400, detail=request.query_params.get("error_description")
        )

    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")

    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    padding = "=" * (4 - len(encoded_state) % 4) if len(encoded_state) % 4 else ""
    padded_state = encoded_state + padding

    # Decode state
    try:
        state_data = json.loads(base64.urlsafe_b64decode(padded_state).decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode state: {str(e)}")

    original_state = state_data.get("state")
    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")

    # Get saved state and verifier from Redis
    saved_state = await get_value_redis(f"hubspot_state:{org_id}:{user_id}")
    code_verifier = await get_value_redis(f"hubspot_verifier:{org_id}:{user_id}")

    if not saved_state:
        raise HTTPException(status_code=400, detail="No saved state found.")

    if original_state != json.loads(saved_state).get("state"):
        raise HTTPException(status_code=400, detail="State does not match.")

    # Exchange temporary auth code for token
    async with httpx.AsyncClient() as client:

        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }

        response = await client.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    token_data = response.json()

    # Save credentials to Redis
    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}", json.dumps(token_data), expire=600
    )

    # Clean up state and verifier
    await asyncio.gather(
        delete_key_redis(f"hubspot_state:{org_id}:{user_id}"),
        delete_key_redis(f"hubspot_verifier:{org_id}:{user_id}"),
    )

    # Close the window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)


# get hubspot credentials from redis to validate the state
async def get_hubspot_credentials(user_id, org_id):
    """

    :param user_id:
    :param org_id:
    :return:
    """
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")

    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")

    try:
        credentials_json = json.loads(credentials)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid credentials format.")

    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")

    return credentials_json


def fetch_items(access_token: str, url: str) -> dict:
    """Fetch data from a given HubSpot API endpoint."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()

async def create_integration_item_metadata_object(data):
    """Create an IntegrationItem metadata object from combined contact and
    account data.
    :param data:
    :return: """
    contact_data = data.get("contact", {})
    account_metadata = data.get("account", {})
    properties = contact_data.get("properties", {})

    return IntegrationItem(
        id=contact_data.get("id"),
        name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
        email=properties.get("email"),
        creation_time=properties.get("createdate"),
        last_modified_time=properties.get("lastmodifieddate"),
        portal_id=account_metadata.get("portalId"),
        ui_domain=account_metadata.get("uiDomain"),
        company_currency=account_metadata.get("companyCurrency"),
    )


async def get_items_hubspot(credentials):
    """Fetch contacts and account details from HubSpot and return as JSON
    response.
    :param credentials:
    :return: """
    credentials = json.loads(credentials)

    contacts_response = fetch_items(credentials.get("access_token"), contacts_url)
    contacts_list = contacts_response.get("results", []) if isinstance(contacts_response, dict) else contacts_response

    account_metadata = fetch_items(credentials.get("access_token"), account_info_url)
    account_metadata = account_metadata[0] if isinstance(account_metadata,
                                                         list) and account_metadata else account_metadata

    combined_data = [{"contact": contact, "account": account_metadata} for contact in contacts_list]

    metadata_objects = [await create_integration_item_metadata_object(data) for data in combined_data]

    response_json = {
        "items": [obj.__dict__ for obj in metadata_objects]
    }

    return json.dumps(response_json)
