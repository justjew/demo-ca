class DomainError(Exception):
    """Base exception for all domain errors."""
    pass

class InvalidModifierError(DomainError):
    """Raised when modifier constraints are violated."""
    pass

class ProductInStopListError(DomainError):
    """Raised when attempting to add a product that's on a stop-list."""
    pass

class DeliveryNotAvailableError(DomainError):
    """Raised when delivery is unavailable for a given address."""
    pass

class InsufficientPointsError(DomainError):
    """Raised when a client does not have enough points."""
    pass

class InvalidStateTransitionError(DomainError):
    """Raised when an illegal transition occurs in the order lifecycle."""
    pass

class OutletNotAcceptingOrdersError(DomainError):
    """Raised when the outlet is not currently accepting orders."""
    pass

class EmptyCartError(DomainError):
    """Raised when attempting to create an order from an empty cart."""
    pass
