from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from datetime import time

class DeliveryMethod(Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"

class OrderStatus(Enum):
    CREATED = "CREATED"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    ACCEPTED = "ACCEPTED"
    READY = "READY"
    TRANSFERRED = "TRANSFERRED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class PaymentStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"

@dataclass(frozen=True, kw_only=True)
class Money:
    amount: int  # Stored in minor units (e.g., cents)
    currency: str = "RUB"
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies do not match")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies do not match")
        return Money(amount=self.amount - other.amount, currency=self.currency)
    
    def __mul__(self, multiplier: float) -> 'Money':
        return Money(amount=int(self.amount * multiplier), currency=self.currency)
    
    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Currencies do not match")
        return self.amount < other.amount
    
    def __le__(self, other: 'Money') -> bool:
        return self < other or self == other
        
    def __gt__(self, other: 'Money') -> bool:
        return not self <= other

@dataclass(frozen=True, kw_only=True)
class Address:
    city: str
    street: str
    building: str
    apartment: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@dataclass(frozen=True, kw_only=True)
class WorkingHours:
    open_time: time
    close_time: time
    
    def is_within(self, t: time) -> bool:
        if self.close_time > self.open_time:
            return self.open_time <= t <= self.close_time
        # Handle overnight schedules
        return t >= self.open_time or t <= self.close_time

@dataclass(frozen=True, kw_only=True)
class Schedule:
    monday: Optional[WorkingHours] = None
    tuesday: Optional[WorkingHours] = None
    wednesday: Optional[WorkingHours] = None
    thursday: Optional[WorkingHours] = None
    friday: Optional[WorkingHours] = None
    saturday: Optional[WorkingHours] = None
    sunday: Optional[WorkingHours] = None

    def get_hours_for_weekday(self, weekday: int) -> Optional[WorkingHours]:
        days = [
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ]
        return days[weekday]
