# Clean Architecture Domain Demo
This project demonstrates the business logic layer of a restaurant platform implementing Clean Architecture principles in pure Python.

## Structure
- `domain/entities`: Core domain aggregates and entities (Cart, Client, Company, Orders).
- `domain/value_objects.py`: Domain value objects (Address, Money, Schedule, OrderStatus).
- `domain/services`: Pure domain computational services (Pricing, Loyalty, Delivery).
- `domain/interfaces`: Abstract ports (Gateways, Repositories).
- `domain/use_cases`: Business operations mapping to domain events.

## Features Implemented
- **Organizational Structure**: Supports hierarchical modeling of `Company` and its subordinate `Outlet`s (physical locations). Each outlet has individual schedules, coverage zones, and order-taking status.
- **Catalog Management**: Groups `Product`s in `Category`s. Features complex `ModifierGroup` rules (min/max selections). Prices and assortment can be overridden globally (Company level) or locally (Outlet level), alongside instantaneous "Stop-lists" for sold-out items.
- **Order Lifecycle**: Handles cart validation, checks delivery availability, enforces modifier boundaries, calculates order totals, processes loyalty points deductions.
- **Loyalty System**: Single profile per customer inside a company. Features dynamic **Loyalty Levels** based on the total amount a customer has historically spent, adjusting the point accrual percentage accordingly.
- **External Integrations**: Includes use cases to handle events from aggregator gateways (`AcceptExternalOrderUseCase`), triggering dispatch of couriers via logistics gateways upon order readiness, and processing transactions and printing receipts through payment and fiscal gateways (`ProcessPaymentUseCase`).

## Testing
The core functional scenarios are verified through a suite of `pytest` unit tests, ensuring robust fulfillment of the technical specification requirements. Run tests using `uv run pytest -v`.
