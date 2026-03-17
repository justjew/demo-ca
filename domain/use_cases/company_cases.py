import uuid
from dataclasses import dataclass

from ..entities.company import Company, LoyaltyLevel
from .crud import CrudUseCase


@dataclass
class LoyaltyLevelDTO:
    name: str
    min_spent_amount: int
    accrual_rate: float


@dataclass
class CompanyCreateDTO:
    name: str
    tax_id: str
    loyalty_levels: list[LoyaltyLevelDTO] | None = None
    max_loyalty_payment_percent: float = 0.50


@dataclass
class CompanyUpdateDTO:
    name: str | None = None
    tax_id: str | None = None
    loyalty_levels: list[LoyaltyLevelDTO] | None = None
    max_loyalty_payment_percent: float | None = None


def _build_levels(dtos: list[LoyaltyLevelDTO]) -> list[LoyaltyLevel]:
    return [
        LoyaltyLevel(
            id=uuid.uuid4(),
            name=d.name,
            min_spent_amount=d.min_spent_amount,
            accrual_rate=d.accrual_rate,
        )
        for d in dtos
    ]


class CompanyCrudUseCase(CrudUseCase[Company, CompanyCreateDTO, CompanyUpdateDTO]):
    entity_name = "Company"

    def _build_entity(self, data: CompanyCreateDTO) -> Company:
        levels = _build_levels(data.loyalty_levels) if data.loyalty_levels else []
        return Company(
            id=uuid.uuid4(),
            name=data.name,
            tax_id=data.tax_id,
            loyalty_levels=levels,
            max_loyalty_payment_percent=data.max_loyalty_payment_percent,
        )

    def _apply_updates(self, entity: Company, data: CompanyUpdateDTO) -> Company:
        if data.name is not None:
            entity.name = data.name
        if data.tax_id is not None:
            entity.tax_id = data.tax_id
        if data.loyalty_levels is not None:
            entity.loyalty_levels = _build_levels(data.loyalty_levels)
        if data.max_loyalty_payment_percent is not None:
            entity.max_loyalty_payment_percent = data.max_loyalty_payment_percent
        return entity
