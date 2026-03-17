import uuid

from ..entities.catalog import ModifierGroup
from ..interfaces.repositories import IOutletRepository, IProductRepository


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
        # Validation checks could be here, but straightforward append for demo
        product.modifier_groups.append(group)
        self.product_repo.save(product)
