from __future__ import annotations

from typing import Optional, List
from abc import ABCMeta
from dataclasses import dataclass, field


class BaseData(object, metaclass=ABCMeta):
    pass


@dataclass(frozen=True)
class EquipmentLength(BaseData):
    length: Optional[float] = None


@dataclass(frozen=True)
class EquipmentVolume(BaseData):
    cubic_capacity: Optional[float] = None


@dataclass(frozen=True)
class EquipmentDimensions(BaseData):
    exterior: Optional[EquipmentLength] = None
    volume: Optional[EquipmentVolume] = None
    tare: Optional[float] = None


@dataclass(frozen=True)
class EquipmentWeight(BaseData):
    gross_maximum: Optional[float] = None
    net_maximum: Optional[float] = None
    tare: Optional[float] = None


@dataclass(frozen=True)
class Equipment(BaseData):
    id: str
    aar_type: Optional[str] = None
    up_type: Optional[str] = None
    weight: Optional[EquipmentWeight] = None
    owner_type_code: Optional[str] = None
    lessee_initial: Optional[str] = None
    dimensions: Optional[EquipmentDimensions] = None


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
    commodities: Optional[List[Commodity]] = None
    load_empty_code: Optional[str] = None
    associated_equipment: Optional[List[str]] = None
    pickup_number: Optional[str] = None
    yard_block: Optional[str] = None
    assessorial_information: Optional[Assessorial] = None


@dataclass(frozen=True)
class Location(BaseData):
    id: str
    city: str
    state_abbreviation: str
    country_abbreviation: Optional[str] = None
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
    route_segments: Optional[List[Segment]] = None
    type_code: Optional[str] = None


@dataclass(frozen=False)
class Route(BaseData):
    origin: CarrierLocation
    destination: CarrierLocation
    route_mileages: Optional[List[RouteMileage]] = None  # not always provided on shipment searches
    id: Optional[str] = None  # id not always provided on shipment searches
    junctions: Optional[List[CarrierLocation]] = None
    last_accomplished_event_stop: Optional[CarrierLocation] = None
    route_str: List[str] = field(init=False)

    def __post_init__(self):
        self.route_str = []
        if self.route_mileages:
            for mileage in self.route_mileages:
                prev_rr = None
                route_str = ""
                for seg in mileage.route_segments:
                    if prev_rr is None:
                        prev_rr = seg.carrier
                        route_str = seg.carrier
                        continue
                    if prev_rr != seg.carrier:
                        if prev_rr == 'UP':
                            # We only care about the next RR interchanging w/ UP
                            route_str += f"-{seg.beginning.junction_abbreviation}-{seg.carrier}"
                        prev_rr = seg.carrier
                self.route_str.append(route_str)


@dataclass(frozen=True)
class CarrierTrain(BaseData):
    section: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[str] = None


@dataclass(frozen=True)
class Event(BaseData):
    type_code: str
    offline: bool
    status_code: str
    event_code: Optional[str] = None
    date_time: Optional[str] = None  # Date of the event in YYYY-MM-DDTHH:MM:SSZ in UTC time format.
    location: Optional[Location] = None
    carrier_abbreviation: Optional[str] = None
    carrier_train: Optional[CarrierTrain] = None
    equipment: Optional[Equipment] = None


@dataclass(frozen=True)
class Shipment(BaseData):
    id: str
    load: Optional[BOL] = None  # Not always available from Case endpoints
    current_event: Optional[Event] = None
    phase_code: Optional[str] = None
    online: Optional[str] = None
    route: Optional[Route] = None
    hold_code: Optional[str] = None
    started_dwell: Optional[str] = None  # The time the shipment began dwell in YYYY-MM-DDTHH:MM:SSZ in UTC time format.
    operational_move_events: Optional[List[Event]] = None


@dataclass(frozen=True)
class User(BaseData):
    user_id: str

@dataclass(frozen=True)
class CaseComment(BaseData):
    body: str
    created_by: User
    created: str  # The time the shipment began dwell in YYYY-MM-DDTHH:MM:SSZ in UTC time format.


@dataclass(frozen=True)
class Case(BaseData):
    id: str
    description: str
    subject: str
    reason_code: str
    status_code: str
    created_by: User
    created: str  # The time the shipment began dwell in YYYY-MM-DDTHH:MM:SSZ in UTC time format.
    last_modified_by: Optional[User] = None
    last_modified: Optional[str] = None  # The time the shipment began dwell in YYYY-MM-DDTHH:MM:SSZ in UTC time format.
    tracked_comments: Optional[List[CaseComment]] = None
    lead_shipment: Optional[Shipment] = None
    lead_equipment: Optional[Equipment] = None
    waybill: Optional[Waybill] = None

