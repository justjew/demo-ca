import uuid
from dataclasses import dataclass, field
from typing import Set, Optional
from datetime import datetime, date, time
from .base import Entity
from ..value_objects import Schedule
from ..exceptions import OutletNotAcceptingOrdersError

@dataclass(kw_only=True)
class Outlet(Entity):
    company_id: uuid.UUID
    name: str
    is_accepting_orders: bool = True
    schedule: Optional[Schedule] = None
    
    # Simple stop-lists: sets of product IDs or modifier option IDs
    product_stop_list: Set[uuid.UUID] = field(default_factory=set)
    modifier_stop_list: Set[uuid.UUID] = field(default_factory=set)
    
    def can_accept_orders(self, current_dt: datetime) -> bool:
        if not self.is_accepting_orders:
            return False
            
        if self.schedule is None:
            return True
            
        weekday = current_dt.weekday()
        current_time = current_dt.time()
        
        hours = self.schedule.get_hours_for_weekday(weekday)
        if not hours:
            return False
            
        return hours.is_within(current_time)

    def is_product_available(self, product_id: uuid.UUID) -> bool:
        return product_id not in self.product_stop_list

    def is_modifier_available(self, modifier_id: uuid.UUID) -> bool:
        return modifier_id not in self.modifier_stop_list

    def add_to_product_stop_list(self, product_id: uuid.UUID) -> None:
        self.product_stop_list.add(product_id)

    def remove_from_product_stop_list(self, product_id: uuid.UUID) -> None:
        self.product_stop_list.discard(product_id)
        
    def add_to_modifier_stop_list(self, modifier_id: uuid.UUID) -> None:
        self.modifier_stop_list.add(modifier_id)
        
    def remove_from_modifier_stop_list(self, modifier_id: uuid.UUID) -> None:
        self.modifier_stop_list.discard(modifier_id)

    def validate_can_order(self, current_dt: datetime) -> None:
        if not self.can_accept_orders(current_dt):
            raise OutletNotAcceptingOrdersError(f"Outlet {self.name} is currently closed or not accepting orders.")
