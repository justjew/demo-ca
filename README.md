# Clean Architecture Domain Demo
This project demonstrates the business logic layer of a restaurant platform implementing Clean Architecture principles in pure Python.

## Structure
- `domain/entities`: Core domain aggregates and entities (Cart, Client, Company, Orders).
- `domain/services`: Pure domain computational services (Pricing, Loyalty).
- `domain/interfaces`: Abstract ports (Gateways, Repositories).
- `domain/use_cases`: Business operations mapping to domain events.
