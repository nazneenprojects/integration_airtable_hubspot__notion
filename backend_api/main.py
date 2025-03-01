"""
main.py
"""

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logging, get_logger
from integrations.airtable.airtable import (
    authorize_airtable,
    oauth2callback_airtable,
    get_airtable_credentials,
    get_items_airtable,
)
from integrations.hubspot.hubspot import (
    authorize_hubspot,
    oauth2callback_hubspot,
    get_hubspot_credentials,
    get_items_hubspot,
)
from integrations.notion.notion import (
    authorize_notion,
    oauth2callback_notion,
    get_notion_credentials,
    get_items_notion,
)


app = FastAPI(
    title="Hubspot Airtable Notion Integration",
    description="REST API endpoints using FastAPI framework",
    version="0.1.0"
)

# set up logging
setup_logging()
logger = get_logger(__name__)

# frontend service running at localhost
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Ping": "Pong"}


# Airtable
@app.post("/integrations/airtable/authorize")
async def authorize_airtable_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    return await authorize_airtable(user_id, org_id)


@app.get("/integrations/airtable/oauth2callback")
async def oauth2callback_airtable_integration(request: Request):
    return await oauth2callback_airtable(request)


@app.post("/integrations/airtable/credentials")
async def get_airtable_credentials_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    return await get_airtable_credentials(user_id, org_id)


@app.post("/integrations/airtable/load")
async def get_airtable_items(credentials: str = Form(...)):
    return await get_items_airtable(credentials)


# Notion
@app.post("/integrations/notion/authorize")
async def authorize_notion_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    return await authorize_notion(user_id, org_id)


@app.get("/integrations/notion/oauth2callback")
async def oauth2callback_notion_integration(request: Request):
    return await oauth2callback_notion(request)


@app.post("/integrations/notion/credentials")
async def get_notion_credentials_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    return await get_notion_credentials(user_id, org_id)


@app.post("/integrations/notion/load")
async def get_notion_items(credentials: str = Form(...)):
    return await get_items_notion(credentials)


# HubSpot
@app.post("/integrations/hubspot/authorize")
async def authorize_hubspot_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    logger.debug(f"call to authorize_hubspot from main ")
    return await authorize_hubspot(user_id, org_id)


@app.get("/integrations/hubspot/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    logger.debug(f"call to oauth2callback_hubspot from main ")
    return await oauth2callback_hubspot(request)


@app.post("/integrations/hubspot/credentials")
async def get_hubspot_credentials_integration(
    user_id: str = Form(...), org_id: str = Form(...)
):
    logger.debug(f"call to get_hubspot_credentials from main ")
    return await get_hubspot_credentials(user_id, org_id)


# Note:
# This api call was initially '/integrations/hubspot/get_hubspot_items' , I renamed it to /integrations/hubspot/load to keep it consistent and to synch with UI logic
# also method name renamed from 'load_slack_data_integration' to 'load_hubspot_data_integration'
@app.post("/integrations/hubspot/load")
async def load_hubspot_data_integration(credentials: str = Form(...)):
    logger.debug(f"call to get_items_hubspot from main ")
    return await get_items_hubspot(credentials)
