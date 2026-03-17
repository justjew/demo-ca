import uuid
from abc import ABC, abstractmethod

from ..entities.catalog import Product
from ..entities.client import Client, LoyaltyProfile
from ..entities.company import Company
from ..entities.order import Order
from ..entities.outlet import Outlet
from .crud_repository import ICrudRepository


class ICompanyRepository(ICrudRepository[Company]):
    """Extends generic CRUD with company-specific queries if needed."""


class IOutletRepository(ICrudRepository[Outlet]):
    """Extends generic CRUD with outlet-specific queries."""

    @abstractmethod
    def list_by_company(self, company_id: uuid.UUID) -> list[Outlet]:
        pass


class IProductRepository(ICrudRepository[Product]):
    """Extends generic CRUD with product-specific queries."""

    @abstractmethod
    def get_many(self, product_ids: list[uuid.UUID]) -> list[Product]:
        pass


class IOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        pass

    @abstractmethod
    def save(self, order: Order) -> None:
        pass


class IClientRepository(ICrudRepository[Client]):
    """Extends generic CRUD with client-specific queries."""

    @abstractmethod
    def get_by_phone(self, phone: str) -> Client | None:
        pass

    @abstractmethod
    def get_loyalty_profile(
        self, client_id: uuid.UUID, company_id: uuid.UUID
    ) -> LoyaltyProfile | None:
        pass

    @abstractmethod
    def save_loyalty_profile(self, profile: LoyaltyProfile) -> None:
        pass

    @abstractmethod
    def save_client(self, client: Client) -> None:
        pass
