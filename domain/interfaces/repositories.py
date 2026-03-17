import uuid
from typing import Optional, List
from abc import ABC, abstractmethod

from ..entities.company import Company
from ..entities.outlet import Outlet
from ..entities.catalog import Product, Category
from ..entities.client import Client, LoyaltyProfile
from ..entities.order import Order

class ICompanyRepository(ABC):
    @abstractmethod
    def get_by_id(self, company_id: uuid.UUID) -> Optional[Company]:
        pass

class IOutletRepository(ABC):
    @abstractmethod
    def get_by_id(self, outlet_id: uuid.UUID) -> Optional[Outlet]:
        pass
        
    @abstractmethod
    def list_by_company(self, company_id: uuid.UUID) -> List[Outlet]:
        pass

class IProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        pass
        
    @abstractmethod
    def get_many(self, product_ids: List[uuid.UUID]) -> List[Product]:
        pass

class IOrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        pass
        
    @abstractmethod
    def save(self, order: Order) -> None:
        pass

class IClientRepository(ABC):
    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[Client]:
        pass
        
    @abstractmethod
    def get_loyalty_profile(self, client_id: uuid.UUID, company_id: uuid.UUID) -> Optional[LoyaltyProfile]:
        pass
        
    @abstractmethod
    def save_loyalty_profile(self, profile: LoyaltyProfile) -> None:
        pass
