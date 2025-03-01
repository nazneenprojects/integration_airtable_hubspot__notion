"""
test_hubspot.py
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Import the function to test
from backend_api.integrations.hubspot.hubspot import authorize_hubspot

# Import the main FastAPI app for testing endpoints
from backend_api.main import app

pytestmark = pytest.mark.asyncio

# Create a test client
client = TestClient(app)

# Mock data for testing
mock_user_id = "TestUser"
mock_org_id = "TestOrg"

# Unit test for authorize_hubspot
@patch('backend_api.integrations.hubspot.hubspot.add_key_value_redis', new_callable=AsyncMock)
async def test_authorize_hubspot(mock_redis):
    result = await authorize_hubspot(mock_user_id, mock_org_id)
    assert "https://app-na2.hubspot.com/oauth/authorize" in result
    assert "client_id" in result
    assert "redirect_uri" in result
