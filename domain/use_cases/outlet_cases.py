import uuid
from dataclasses import dataclass
from datetime import time

from ..entities.outlet import Outlet
from ..value_objects import Money, Schedule, WorkingHours
from .crud import CrudUseCase


@dataclass
class WorkingHoursDTO:
    open_time: str
    close_time: str


@dataclass
class ScheduleDTO:
    monday: WorkingHoursDTO | None = None
    tuesday: WorkingHoursDTO | None = None
    wednesday: WorkingHoursDTO | None = None
    thursday: WorkingHoursDTO | None = None
    friday: WorkingHoursDTO | None = None
    saturday: WorkingHoursDTO | None = None
    sunday: WorkingHoursDTO | None = None


@dataclass
class MoneyDTO:
    amount: int
    currency: str


@dataclass
class OutletCreateDTO:
    company_id: uuid.UUID
    name: str
    is_accepting_orders: bool = True
    schedule: ScheduleDTO | None = None


@dataclass
class OutletUpdateDTO:
    name: str | None = None
    is_accepting_orders: bool | None = None
    schedule: ScheduleDTO | None = None
    product_price_overrides: dict[uuid.UUID, MoneyDTO] | None = None
    modifier_price_overrides: dict[uuid.UUID, MoneyDTO] | None = None


_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _build_schedule(dto: ScheduleDTO) -> Schedule:
    kwargs = {}
    for day in _DAYS:
        day_dto = getattr(dto, day)
        if day_dto:
            kwargs[day] = WorkingHours(
                open_time=time.fromisoformat(day_dto.open_time),
                close_time=time.fromisoformat(day_dto.close_time),
            )
    return Schedule(**kwargs)


def _build_overrides(data: dict[uuid.UUID, MoneyDTO]) -> dict[uuid.UUID, Money]:
    return {k: Money(amount=v.amount, currency=v.currency) for k, v in data.items()}


class OutletCrudUseCase(CrudUseCase[Outlet, OutletCreateDTO, OutletUpdateDTO]):
    entity_name = "Outlet"

    def _build_entity(self, data: OutletCreateDTO) -> Outlet:
        return Outlet(
            id=uuid.uuid4(),
            company_id=data.company_id,
            name=data.name,
            is_accepting_orders=data.is_accepting_orders,
            schedule=_build_schedule(data.schedule) if data.schedule else None,
        )

    def _apply_updates(self, entity: Outlet, data: OutletUpdateDTO) -> Outlet:
        if data.name is not None:
            entity.name = data.name
        if data.is_accepting_orders is not None:
            entity.is_accepting_orders = data.is_accepting_orders
        if data.schedule is not None:
            entity.schedule = _build_schedule(data.schedule)
        if data.product_price_overrides is not None:
            entity.product_price_overrides = _build_overrides(
                data.product_price_overrides
            )
        if data.modifier_price_overrides is not None:
            entity.modifier_price_overrides = _build_overrides(
                data.modifier_price_overrides
            )
        return entity
