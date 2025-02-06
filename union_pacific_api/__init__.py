import os
import json
from datetime import timedelta
from dataclasses import fields
from typing import Optional
from urllib.parse import urlencode
import requests
from datetime import datetime
import base64
import dotenv
from dacite import from_dict

from union_pacific_api.datatypes import BaseData, Route, Location, Shipment


class UPClient:
    base_url = 'https://customer.api.up.com'
    route_endpoint = '/services/v2/routes'
    locations_endpoint = '/services/v2/locations'
    shipments_endpoint = '/services/v2/shipments'
    cases_endpoint = '/services/v2/cases'
    oauth_endpoint = '/oauth/token'
    token_filename = '.token'
    env_filename = '.env'

    def __init__(self, userid: str = None, password: str = None, env_dir: str = None, force_new_token: bool = False):
        if env_dir:
            self._env_dir = env_dir
        else:
            self._env_dir = os.getcwd()

        if userid and password:
            self._uid = userid
            self._pw = password
        else:
            # get credentials from .env file
            self._load_env_credentials()

        self._session = requests
        self._tk = None
        self._session = None
        self._tk_path = None
        self._tk_datetime = None
        self._force_new_token = force_new_token

        if not os.path.exists(os.path.join(self._env_dir, self.token_filename)):
            with open(os.path.join(self._env_dir, self.token_filename), "w") as f:
                f.write("# Automatically created ***DO NOT EDIT***\n")
                f.write("UP_TOKEN=\n")
                f.write("UP_TOKEN_TIMESTAMP=\n")
        else:
            self._load_env_token()

    def _load_env_credentials(self) -> None:
        dotenv.load_dotenv(os.path.join(self._env_dir, self.env_filename))
        self._uid = os.getenv('UP_ACCESSID')
        self._pw = os.getenv('UP_SECRET_KEY')

        if not self._uid or not self._pw:
            raise Exception(f"""
            Unable to find UP credentials environment variables. Please ensure a .env file is
            present in the {self._env_dir} directory with UI_USERID and UI_PASSWORD set.  Or provide
            credentials in class instance.
            """)

    def _load_env_token(self) -> None:
        dotenv.load_dotenv(os.path.join(self._env_dir, self.token_filename))
        _tk_timestamp = os.getenv('UP_TOKEN_TIMESTAMP')
        if _tk_timestamp and not self._force_new_token:
            self._tk_datetime = datetime.fromisoformat(_tk_timestamp)
            self._tk = os.getenv('UP_TOKEN')

    @property
    def token(self) -> Optional[str]:
        if self._tk:
            if datetime.now() > self._tk_datetime + timedelta(hours=2):
                print(f"Old token out of date: {self._tk_datetime}")
                self._tk = self._request_token()
        else:
            self._tk = self._request_token()
        return self._tk

    @token.setter
    def token(self, tk) -> None:
        if self._tk != tk:
            print(f"New token set: {tk}")
            _path = os.path.join(self._env_dir, self.token_filename)
            _iso_date = datetime.now() if tk else ""
            # set timestamp env variable in iso format
            dotenv.set_key(_path, "UP_TOKEN_TIMESTAMP", str(_iso_date))
            self._tk_datetime = _iso_date
            # set token
            dotenv.set_key(_path, "UP_TOKEN", tk)
            self._tk = tk

    def _request_token(self):
        """
        Retrieve Authorization Token
        The OAuth Token service can be used to retrieve this token, which is valid for two hours.
        It is best to cache this value and reuse it for as long as it is valid, as multiple calls
        to the Oauth Token service will result in an error.
        :return: string token
        """
        url = self.endpoint_builder(self.oauth_endpoint)
        message = self._uid + ':' + self._pw
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')

        payload = 'grant_type=client_credentials'
        headers = {
            'Authorization': 'Basic ' + base64_message,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        resp = requests.request("POST", url, headers=headers, data=payload)
        if resp.status_code != 200:
            raise Exception(f"Token request failed. Status Code: {resp.status_code}")
        r_json = resp.json()
        self.token = r_json['access_token']
        return self.token

    def endpoint_builder(self, endpoint: str, **kwargs):
        """
        Builds union_pacific_api url as string
        :param endpoint: union_pacific_api request type endpoint
        :param kwargs: URL parameters (key/value pairs)
        :return: URL string
        """
        # Remove any items with a value of None
        is_not_none = {k: v for k, v in kwargs.items() if v is not None}
        return f"{self.base_url}{endpoint}?{urlencode(is_not_none)}"

    def _call_api(self, url):
        """
        Call a Union Pacific API and return JSON response
        :param url: API Base URL
        :return: Response json object
        """
        now = datetime.now()
        dt = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {}
        headers = {'Authorization': 'Bearer ' + self.token, 'Date': dt}
        resp = requests.request("GET", url, headers=headers, data=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"\nReceived unexpected response from UP API {url};"
                            f"\nStatus Code: {resp.status_code};"
                            f"\nResponse: {resp.text}")

    def get_routes(self, origin_id, dest_id, origin_rr: Optional[str] = None, dest_rr: Optional[str] = None,
                   jct_abbr: Optional[str] = None, jct_rr: Optional[str] = None) -> list[Route]:
        """
        Find all applicable routes given a set of criteria. Origin and Destination Location Id are required.
        Junction carriers can only be provided if at least one junction is given. Provided junction
        carriers will be applied to all given junctions.

        :param origin_id: origin location id (Required)
        :param dest_id: destination location id (Required)
        :param origin_rr: origin carrier
        :param dest_rr: destination carrier
        :param jct_abbr: gateway junction abbreviation
        :param jct_rr: gateway junction carrier
        :return: List of route objects
        """
        # Set optional URL parameters
        optional_params = {
            'origin_carrier': origin_rr,
            'destination_carrier': dest_rr,
            'junction_abbreviation': jct_abbr,
            'junction_carrier': jct_rr
        }
        url = self.endpoint_builder(self.route_endpoint, origin_id=origin_id, destination_id=dest_id, **optional_params)
        r_json = self._call_api(url)

        # json_formatted_str = json.dumps(r_json, indent=2)
        # print(json_formatted_str)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Route)]  # noqa

        resp = []
        for rt in r_json:
            resp.append(from_dict(Route, {k: rt[k] for k in data_keys if k in rt.keys()}))
        return resp

    def get_route_by_id(self, route_id: str) -> Route:
        """
        Return the details of a route by Id. Details include the segments of the Route.

        :param route_id: UP route id (required)
        :return: a Route object
        """
        url = self.endpoint_builder(f"{self.route_endpoint}/{route_id}")
        r_json = self._call_api(url)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Route)]  # noqa
        return from_dict(Route, {k: r_json[k] for k in data_keys if k in r_json.keys()})

    def get_locations(self, splc: Optional[str] = None) -> list[Location]:
        """
        If no parameters are passed, all authorized locations associated with the user if no parameters are passed.
        Searching by SPLC includes a GENERAL location which represents the entirety of the area covered by the SPLC
        in addition to any authorized locations. Track data will not be populated, use the detail service for tracks.

        :param splc: location splc (Optional)
        :return: List of Location objects
        """
        # add padding
        _splc = splc.ljust(9, '0') if splc else None
        url = self.endpoint_builder(self.locations_endpoint, splc=_splc)
        r_json = self._call_api(url)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Location)]  # noqa

        resp = []
        for loc in r_json:
            resp.append(from_dict(Location, {k: loc[k] for k in data_keys if k in loc.keys()}))
        return resp

    def get_location_by_id(self, location_id: str) -> Location:
        """
        Using this detail service will return the Tracks and its capacity at facilities with Tracks.

        :param location_id: UP location id (required)
        :return: a Location object
        """
        url = self.endpoint_builder(f"{self.locations_endpoint}/{location_id}")
        r_json = self._call_api(url)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Location)]  # noqa
        return from_dict(Location, {k: r_json[k] for k in data_keys if k in r_json.keys()})

    def get_shipments(
            self,
            equipment_ids: Optional[list[str]] = None,
            waybill_ids: Optional[list[str]] = None,
            origin_id: Optional[list[str]] = None,
            destination_id: Optional[list[str]] = None,
            phase_codes: Optional[list[str]] = None
    ) -> list[Shipment]:
        """
        This service can be used to retrieve requested Shipments for which the user is party to the bill.
        A shipment represents the delivery of a loaded or empty rail equipment from origin to destination.
        The shipment ID is a unique number created for the shipment and is not equipment id.

        Parameters, in any combination and quantity, can be used to narrow the search. If no parameters
        are passed, all active Shipments of the user will be returned. The detail service can be used if
        all events are desired for a particular shipment.

        Due to the potential amount of Shipments that can can be returned from a single request, the Shipments
        may have differing amounts of details depending on the number of records returned. A maximum of 17,500
        shipments can be returned. The attributes returned for each record according to the payload size
        is listed here:

            - With up to 2,000 records: All available attributes
            - With up to 10,000 records: id, load, route, eta, eti, etg, current_event, phase_code
            - Above 10,000 records: id, load (with equipment id and waybill id only), phase_code

        :param equipment_ids: list of equipment ids (Optional)
        :param waybill_ids: list of waybill ids (Optional)
        :param origin_id: list of UP location ids for shipment origins (Optional)
        :param destination_id: list of UP location ids for shipment destinations (Optional)
        :param phase_codes: list of UP phase_codes (i.e. ENROUTE) (Optional)
        :return: List of Location objects
        """
        # Set optional URL parameters
        optional_params = {
            'equipment_id': equipment_ids,
            'waybill_id': waybill_ids,
            'origin_location_id': origin_id,
            'destination_location_id': destination_id,
            'phase_codes': phase_codes
        }
        url = self.endpoint_builder(self.shipments_endpoint, **optional_params)
        r_json = self._call_api(url)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Shipment)]  # noqa

        resp = []
        for shp in r_json:
            resp.append(from_dict(Shipment, {k: shp[k] for k in data_keys if k in shp.keys()}))
        return resp

    def get_shipment_by_id(self, shipment_id: Optional[str] = None) -> Shipment:
        """
        Returns shipments for which the user is party to the bill. A shipment represents the delivery
        of a loaded or empty rail equipment from origin to destination. The shipment ID is a unique number
        created for the shipment and is not equipment id.

        A note when using operational move events: Each event has a location with an id. Those event location
        ids, especially those outside of the UP rail network, may not return any results when used in
        conjunction with the origin_location_id and destination_location_id parameters of /services/v2/shipments

        :param shipment_id: UP shipment id number (required)
        :return: Shipment object
        """
        url = self.endpoint_builder(f"{self.shipments_endpoint}/{shipment_id}")
        r_json = self._call_api(url)

        # Remove any data fields that are not in dataclass
        data_keys = [f.name for f in fields(Shipment)]  # noqa
        return from_dict(Shipment, {k: r_json[k] for k in data_keys if k in r_json.keys()})

    def get_case_by_id(self, case_id: str):
        """
        :param case_id: Use to get a single case details.
        :return:
        """
        url = self.endpoint_builder(f"{self.cases_endpoint}/{case_id}")
        r_json = self._call_api(url)
        return r_json

    def get_cases(self, created: Optional[list[str]] = None, status_codes: Optional[list[str]] = None,
                  equipment_ids: Optional[list[str]] = None):
        """
        If no parameters are given will return all "OPEN" Cases.

        :param created: Array of strings <date>
        :param status_codes: Array of strings. Can provide specific status code or OPEN to retrieve all open cases
            (IN_PROGRESS, NEW, AWAITING_FEEDBACK) or CEASED to retrieve ceased cases (CANCELED, CLOSED)
        :param equipment_ids: Array of equipment id strings
        :return: List of Case Objects
        """
        # Set optional URL parameters
        optional_params = {
            'equipment_id': equipment_ids,
            'status_code': status_codes,
            'created': created
        }
        url = self.endpoint_builder(f"{self.cases_endpoint}", **optional_params)
        r_json = self._call_api(url)
        return r_json

    def get_single_departure(self, departure_id):
        """
        Allows searching for a single departure by the ID. Returns one departure only.

        :param departure_id:
        :return:
        """
        pass

    def get_departures(self, departure_id, origin_location_id, dest_location_id):
        """
        Finds departures for origin to destination by time and origin/destination location id. If departure IDs are provided, any
        other parameters will be ignored. Time is limited to 7 days of departures, and if no times are given only the next 7 days
        will be given.

        :param departure_id:
        :param origin_location_id:
        :param dest_location_id:
        :return:
        """
        pass