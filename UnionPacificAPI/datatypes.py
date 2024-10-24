from typing import Optional
from abc import ABCMeta
from dataclasses import dataclass


class BaseData(object, metaclass=ABCMeta):
    pass


@dataclass(frozen=True)
class EquipmentWeight(BaseData):
    gross_maximum: Optional[float] = None
    net_maximum: Optional[float] = None
    tare: Optional[float] = None


@dataclass(frozen=True)
class Equipment(BaseData):
    id: str
    aar_type: Optional[str] = None
    weight: Optional[EquipmentWeight] = None
    owner_type_code: Optional[str] = None
    lessee_initial: Optional[str] = None


@dataclass(frozen=True)
class Commodity(BaseData):
    stcc: str
    description: Optional[str] = None


@dataclass(frozen=True)
class Waybill(BaseData):
    id: str
    primary_reference_id: Optional[str] = None
    primary_reference_id_type_code: Optional[str] = None
    waybill_number: Optional[str] = None
    waybill_date: Optional[str] = None  # YYYY-MM-DD format


@dataclass(frozen=True)
class Assessorial(BaseData):
    storage_first_chargeable_day: str


@dataclass(frozen=True)
class BOL(BaseData):
    equipment: Equipment
    waybill: Optional[Waybill] = None
    commodities: Optional[list[Commodity]] = None
    load_empty_code: Optional[str] = None
    associated_equipment: Optional[list[str]] = None
    pickup_number: Optional[str] = None
    yard_block: Optional[str] = None
    assessorial_information: Optional[Assessorial] = None


@dataclass(frozen=True)
class Location(BaseData):
    id: str
    city: str
    state_abbreviation: str
    country_abbreviation: str
    type_code: Optional[str] = None
    splc: Optional[str] = None
    # Following only provided when request by ID
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass(frozen=True)
class CarrierLocation(BaseData):
    location: Location
    carrier: Optional[str] = None
    junction_abbreviation: Optional[str] = None


@dataclass(frozen=True)
class Segment(BaseData):
    beginning: CarrierLocation
    end: CarrierLocation
    mileage: float
    carrier: Optional[str] = None


@dataclass(frozen=True)
class RouteMileage(BaseData):
    mileage: float
    segments: Optional[list[Segment]] = None
    type_code: Optional[str] = None


@dataclass(frozen=True)
class Route(BaseData):
    id: str
    origin: CarrierLocation
    destination: CarrierLocation
    junctions: list[CarrierLocation]
    route_mileages: list[RouteMileage]


@dataclass(frozen=True)
class CarrierTrain(BaseData):
    section: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[str] = None


@dataclass(frozen=True)
class Event(BaseData):
    type_code: str
    offline: str
    status_code: str
    event_code: Optional[str] = None
    date_time: Optional[str] = None  # Date of the event in YYYY-MM-DDTHH:MM:SSZ in UTC time format.
    location: Optional[Location] = None
    carrier_abbreviation: Optional[str] = None
    carrier_train: Optional[CarrierTrain] = None


@dataclass(frozen=True)
class Shipment(BaseData):
    id: str
    load: BOL
    current_event: Optional[Event] = None
    phase_code: Optional[str] = None
    online: Optional[str] = None
    route: Optional[Route] = None
    hold_code: Optional[str] = None
    started_dwell: Optional[str] = None  # The time the shipment began dwell in YYYY-MM-DDTHH:MM:SSZ in UTC time format.