import uuid
from dataclasses import dataclass

from ..entities.catalog import ModifierGroup, Product
from ..interfaces.repositories import IOutletRepository, IProductRepository
from ..value_objects import Money
from .crud import CrudUseCase


class ManageStopListUseCase:
    def __init__(self, outlet_repo: IOutletRepository):
        self.outlet_repo = outlet_repo

    def add_product_to_stop_list(
        self, outlet_id: uuid.UUID, product_id: uuid.UUID
    ) -> None:
        outlet = self.outlet_repo.get_by_id(outlet_id)
        if not outlet:
            return
        outlet.add_to_product_stop_list(product_id)
        self.outlet_repo.save(outlet)

    def remove_product_from_stop_list(
        self, outlet_id: uuid.UUID, product_id: uuid.UUID
    ) -> None:
        outlet = self.outlet_repo.get_by_id(outlet_id)
        if not outlet:
            return
        outlet.remove_from_product_stop_list(product_id)
        self.outlet_repo.save(outlet)


class ConfigureModifiersUseCase:
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo

    def add_modifier_group(self, product_id: uuid.UUID, group: ModifierGroup) -> None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return
        product.modifier_groups.append(group)
        self.product_repo.save(product)


@dataclass
class ProductCreateDTO:
    name: str
    description: str
    base_price_amount: int
    base_price_currency: str
    category_id: uuid.UUID
    is_active: bool = True


@dataclass
class ProductUpdateDTO:
    name: str | None = None
    description: str | None = None
    base_price_amount: int | None = None
    base_price_currency: str | None = None
    category_id: uuid.UUID | None = None
    is_active: bool | None = None


class ProductCrudUseCase(CrudUseCase[Product, ProductCreateDTO, ProductUpdateDTO]):
    entity_name = "Product"

    def _build_entity(self, data: ProductCreateDTO) -> Product:
        return Product(
            id=uuid.uuid4(),
            name=data.name,
            description=data.description,
            base_price=Money(
                amount=data.base_price_amount, currency=data.base_price_currency
            ),
            category_id=data.category_id,
            is_active=data.is_active,
        )

    def _apply_updates(self, entity: Product, data: ProductUpdateDTO) -> Product:
        if data.name is not None:
            entity.name = data.name
        if data.description is not None:
            entity.description = data.description
        if data.base_price_amount is not None or data.base_price_currency is not None:
            entity.base_price = Money(
                amount=data.base_price_amount
                if data.base_price_amount is not None
                else entity.base_price.amount,
                currency=data.base_price_currency
                if data.base_price_currency is not None
                else entity.base_price.currency,
            )
        if data.category_id is not None:
            entity.category_id = data.category_id
        if data.is_active is not None:
            entity.is_active = data.is_active
        return entity
