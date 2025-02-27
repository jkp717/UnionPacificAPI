# test_union_pacific.py
import pytest
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from union_pacific_api import UPClient
from union_pacific_api.datatypes import (
    Route,
    Location,
    Shipment,
    Case,
    Waybill,
    Equipment
)


# ---- Custom Request Mocking ----
@pytest.fixture
def mock_requests():
    """Custom requests mock fixture using unittest.mock"""
    mock_responses = {}

    def _add_mock_response(
            method: str,
            url: str,
            status_code: int = 200,
            json_data: dict = None,
            text: str = None
    ):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        mock_response.text = text or ""
        mock_responses[(method.upper(), url)] = mock_response

    with patch('requests.Session.send') as mock_send:
        def _mock_send_implementation(request, **kwargs):
            key = (request.method.upper(), request.url.split('?')[0])
            if key in mock_responses:
                return mock_responses[key]
            raise ConnectionError(f"No mock response for {request.method} {request.url.split('?')[0]}")

        mock_send.side_effect = _mock_send_implementation
        yield _add_mock_response


# ---- Client Fixtures ----
@pytest.fixture
def mock_client_dataclass(mock_requests):
    """Client with dataclass conversion enabled"""
    client = UPClient(
        userid="test_user",
        password="test_pass",
        use_dataclasses=True
    )

    # Mock token endpoint
    mock_requests(
        method="POST",
        url=f"{UPClient.base_url}{UPClient.oauth_endpoint}",
        json_data={"access_token": "test_token", "expires_in": 7200},
    )

    client.get_new_token()  # Force token initialization
    return client


@pytest.fixture
def mock_client_json(mock_requests):
    """Client with raw JSON responses"""
    client = UPClient(
        userid="test_user",
        password="test_pass",
        use_dataclasses=False
    )

    # Mock token endpoint
    mock_requests(
        method="POST",
        url=f"{UPClient.base_url}{UPClient.oauth_endpoint}",
        json_data={"access_token": "test_token", "expires_in": 7200},
    )

    client.get_new_token()  # Force token initialization
    return client


# ---- Mock Data Templates ----
MOCK_DATA = {
    "route": {
        "id": "RT-001",
        "origin": {
            "location": {
                "id": "LOC-OMAH",
                "city": "Omaha",
                "state_abbreviation": "NE"
            }
        },
        "destination": {
            "location": {
                "id": "LOC-CHI",
                "city": "Chicago",
                "state_abbreviation": "IL"
            }
        }
    },
    "location": {
        "id": "LOC-OMAH",
        "city": "Omaha",
        "state_abbreviation": "NE"
    },
    "equipment": {
        "id": "EQ-001",
        "aar_type": "BOX"
    },
    "shipment": {
        "id": "SH-001",
        "load": {
            "equipment": {
                "id": "EQ-001"
            }
        },
        "phase_code": "ENROUTE"
    }
}


# ---- Parameterized Tests ----
@pytest.mark.parametrize("client_fixture", ["mock_client_dataclass", "mock_client_json"])
def test_route_by_id_endpoint(client_fixture, request, mock_requests):
    """Test route endpoint for both client types"""
    client = request.getfixturevalue(client_fixture)

    # Setup mock
    mock_requests(
        method="GET",
        url=f"{UPClient.base_url}{UPClient.route_endpoint}/RT-001",
        json_data=MOCK_DATA["route"]
    )

    result = client.get_route_by_id("RT-001")

    # Validate response format
    if client.use_dataclasses:
        assert isinstance(result, Route)
        assert result.origin.location.city == "Omaha"
    else:
        assert isinstance(result, dict)
        assert result["origin"]["location"]["city"] == "Omaha"


@pytest.mark.parametrize("client_fixture", ["mock_client_dataclass", "mock_client_json"])
def test_routes_endpoint(client_fixture, request, mock_requests):
    """Test routes endpoint for both client types"""
    client = request.getfixturevalue(client_fixture)

    # Setup mock
    mock_requests(
        method="GET",
        url=f"{UPClient.base_url}{UPClient.route_endpoint}",
        json_data=[MOCK_DATA["route"]]  # noqa
    )
    result = client.get_routes(origin_id="ORIG1", dest_id="DEST1")

    # Validate response format
    if client.use_dataclasses:
        assert isinstance(result, list)
        assert isinstance(result[0], Route)
        assert result[0].origin.location.city == "Omaha"
    else:
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert result[0]["origin"]["location"]["city"] == "Omaha"


@pytest.mark.parametrize("client_fixture", ["mock_client_dataclass", "mock_client_json"])
def test_location_by_id_endpoint(client_fixture, request, mock_requests):
    """Test location endpoint for both client types"""
    client = request.getfixturevalue(client_fixture)

    # Setup mock
    mock_requests(
        method="GET",
        url=f"{UPClient.base_url}{UPClient.locations_endpoint}/LOC-OMAH",
        json_data=MOCK_DATA["location"]
    )

    result = client.get_location_by_id("LOC-OMAH")

    # Validate response format
    if client.use_dataclasses:
        assert isinstance(result, Location)
        assert result.state_abbreviation == "NE"
    else:
        assert isinstance(result, dict)
        assert result["state_abbreviation"] == "NE"


@pytest.mark.parametrize("client_fixture", ["mock_client_dataclass", "mock_client_json"])
def test_locations_endpoint(client_fixture, request, mock_requests):
    """Test routes endpoint for both client types"""
    client = request.getfixturevalue(client_fixture)

    # Setup mock
    mock_requests(
        method="GET",
        url=f"{UPClient.base_url}{UPClient.locations_endpoint}",
        json_data=[MOCK_DATA["location"]]  # noqa
    )
    result = client.get_locations()

    # Validate response format
    if client.use_dataclasses:
        assert isinstance(result, list)
        assert isinstance(result[0], Location)
        assert result[0].city == "Omaha"
    else:
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert result[0]["city"] == "Omaha"


# ---- Error Handling Test ----
def test_error_response(mock_client_dataclass, mock_requests):
    """Test error handling for both client types"""
    mock_requests(
        method="GET",
        url=f"{UPClient.base_url}{UPClient.route_endpoint}/INVALID",
        status_code=404,
        text="Not Found"
    )

    with pytest.raises(Exception) as exc_info:
        mock_client_dataclass.get_route_by_id("INVALID")

    assert "unexpected response" in str(exc_info.value)
    assert "404" in str(exc_info.value)


# ---- Token Tests ----
def test_token_renewal(mock_client_dataclass, mock_requests):
    """Test token renewal logic"""
    # Set expired token
    mock_client_dataclass._tk_datetime = datetime.now() - timedelta(hours=3)

    # Mock new token request
    mock_requests(
        method="POST",
        url=f"{UPClient.base_url}{UPClient.oauth_endpoint}",
        json_data={"access_token": "new_token", "expires_in": 7200},
    )

    assert mock_client_dataclass.token == "new_token"