from ..value_objects import Address
from ..entities.outlet import Outlet

class DeliveryService:
    """Domain service for checking delivery coverage."""
    
    @staticmethod
    def is_address_covered(address: Address, outlet: Outlet) -> bool:
        """
        Determines if the given address is within the outlet's delivery zone.
        In a real application, this would involve geocoding and polygon intersection.
        For domain purposes, assume it passes or depends on Address fields.
        """
        # Simplistic stub: assume all addresses in same city are covered
        # or we implement real coordinate logic here later.
        if not address.city:
            return False
            
        return True
