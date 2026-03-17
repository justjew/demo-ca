import uuid
from abc import ABC, abstractmethod

from ..entities.catalog import Product
from ..entities.client import Client, LoyaltyProfile
from ..entities.company import Company
from ..entities.order import Order
from ..entities.outlet import Outlet


class ICompanyRepository(ABC):
    @abstractmethod
    def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        pass

    @abstractmethod
    def save(self, company: Company) -> None:
        pass

class IOutletRepository(ABC):
    @abstractmethod
    def get_by_id(self, outlet_id: uuid.UUID) -> Outlet | None:
        pass

    @abstractmethod
    def list_by_company(self, company_id: uuid.UUID) -> list[Outlet]:
        pass

    @abstractmethod
    def save(self, outlet: Outlet) -> None:
        pass

class IProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        pass

    @abstractmethod
    def get_many(self, product_ids: list[uuid.UUID]) -> list[Product]:
        pass

    @abstractmethod
    def save(self, product: Product) -> None:
        pass

class IOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        pass

    @abstractmethod
    def save(self, order: Order) -> None:
        pass

class IClientRepository(ABC):
    @abstractmethod
    def get_by_phone(self, phone: str) -> Client | None:
        pass

    @abstractmethod
    def get_loyalty_profile(self, client_id: uuid.UUID, company_id: uuid.UUID) -> LoyaltyProfile | None:
        pass

    @abstractmethod
    def save_loyalty_profile(self, profile: LoyaltyProfile) -> None:
        pass
