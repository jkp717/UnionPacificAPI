import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import os
from union_pacific_api import UPClient
from union_pacific_api.datatypes import Route, Location, Shipment, Case, Waybill, Equipment, CarrierLocation


class TestUPClient(unittest.TestCase):
    def setUp(self):
        # Base mock data structure
        self.base_location_data = {
            "id": "LOC123",
            "city": "TestCity",
            "state_abbreviation": "TS",
            "country_abbreviation": "US",
            "type_code": "RAIL",
            "splc": "123456789"
        }

        # Configure mock response
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = [self.base_location_data]
        self.mock_response.status_code = 200

        # Patch requests and environment
        self.patcher_get = patch('requests.request', return_value=self.mock_response)
        self.patcher_env = patch.dict(os.environ, {
            'UP_ACCESSID': 'test_user',
            'UP_SECRET_KEY': 'test_pass',
            'UP_TOKEN': 'test_token',
            'UP_TOKEN_TIMESTAMP': datetime.now().isoformat()
        })

        self.mock_get = self.patcher_get.start()
        self.patcher_env.start()

        # Initialize client
        self.client = UPClient(use_dataclasses=True)
        self.client._tk = 'mock_token'
        self.client._tk_datetime = datetime.now()

    def tearDown(self):
        self.patcher_get.stop()
        self.patcher_env.stop()

    def test_initialization(self):
        client = UPClient(userid="test", password="test")
        self.assertEqual(client._uid, "test")
        self.assertEqual(client._pw, "test")

    def test_token_management(self):
        # Create token-specific mock response
        token_response = Mock()
        token_response.json.return_value = {'access_token': 'new_token'}
        token_response.status_code = 200

        # Temporarily override the mock
        original_mock = self.mock_get.return_value
        self.mock_get.return_value = token_response

        # Test token refresh
        self.client._tk_datetime = datetime.now() - timedelta(hours=3)
        token = self.client.token
        self.assertEqual(token, 'new_token')

        # Restore original mock
        self.mock_get.return_value = original_mock

    def test_endpoint_builder(self):
        url = self.client.endpoint_builder('/test', param1='val1', param2=['a', 'b'])
        self.assertIn('param1=val1', url)
        self.assertIn('param2=a%2Cb', url)

    def test_get_routes(self):
        # Test with dataclasses
        result = self.client.get_routes(origin_id="ORIG1", dest_id="DEST1")
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], Route)

        # Test with raw JSON
        self.client.use_dataclasses = False
        result = self.client.get_routes(origin_id="ORIG1", dest_id="DEST1")
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], dict)

    def test_get_route_by_id(self):
        # Complete route mock data
        route_data = {
            "id": "ROUTE123",
            "origin": {
                "location": self.base_location_data,
                "carrier": "UP",
                "junction_abbreviation": None
            },
            "destination": {
                "location": self.base_location_data,
                "carrier": "UP",
                "junction_abbreviation": None
            },
            "route_mileages": [{
                "mileage": 150.5,
                "type_code": "MAIN",
                "route_segments": []
            }]
        }

        # Override mock response
        original_mock = self.mock_response.json.return_value
        self.mock_response.json.return_value = route_data

        result = self.client.get_route_by_id("ROUTE123")
        self.assertIsInstance(result, Route)
        self.assertEqual(result.id, "ROUTE123")

        # Restore mock
        self.mock_response.json.return_value = original_mock

    def test_get_locations(self):
        result = self.client.get_locations(splc="1234567")
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], Location)

    def test_get_location_by_id(self):
        result = self.client.get_location_by_id("LOC123")
        self.assertIsInstance(result, Location)

    def test_get_shipments(self):
        # Mock shipment data
        self.mock_response.json.return_value = [{
            "id": "SHIP123",
            "phase_code": "ENROUTE",
            "current_event": {
                "type_code": "DEPARTURE",
                "offline": False,
                "status_code": "COMPLETED"
            }
        }]

        result = self.client.get_shipments(equipment_ids=["EQ123"])
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], Shipment)

    def test_get_shipment_by_id(self):
        self.mock_response.json.return_value = {
            "id": "SHIP123",
            "phase_code": "ENROUTE",
            "current_event": {
                "type_code": "DEPARTURE",
                "offline": False,
                "status_code": "COMPLETED"
            }
        }

        result = self.client.get_shipment_by_id("SHIP123")
        self.assertIsInstance(result, Shipment)

    def test_error_handling(self):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Server Error"
        self.mock_get.return_value = error_response

        with self.assertRaises(Exception) as context:
            self.client.get_routes(origin_id="ORIG1", dest_id="DEST1")
        self.assertIn("unexpected response", str(context.exception))

    def test_dataclass_conversion(self):
        test_data = [{
            "id": "TEST1",
            "city": "TestCity",
            "state_abbreviation": "TS",
            "country_abbreviation": "US",
            "extra_field": "ignore"
        }]

        result = self.client._json_to_dataclass(test_data, Location)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0].id, "TEST1")
        self.assertFalse(hasattr(result[0], 'extra_field'))


if __name__ == '__main__':
    unittest.main()