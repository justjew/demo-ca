# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-03-17

### Added
- External order processing via `AcceptExternalOrderUseCase` and `IExternalOrderGateway`.
- `ProcessPaymentUseCase` to facilitate order payments, interacting with `IPaymentGateway`.
- Automatic fiscal receipt generation via `IFiscalGateway` upon successful payment.
- External tracking links integration (`delivery_tracking_id`, `receipt_id`, `external_id`) into the `Order` aggregate.
- Automated courier request creation triggering `ILogisticsGateway.request_courier` when a delivery order transitions to the `READY` state.

## [0.3.0] - 2026-03-17

### Added
- `LoyaltyLevel` entity to establish dynamic point accrual tiers.

### Changed
- `Company` accrual system shifted from a static percentage (`loyalty_accrual_rate`) to dynamic rate calculation evaluating the client's historically spent amount against available `loyalty_levels`.
- `LoyaltyService.calculate_accrual` now accepts `total_spent` to resolve the accurate level rate.

## [0.2.0] - 2026-03-17

### Added
- Localized assortment control on the `Outlet` level (`local_assortment`).
- Product and modifier price overrides dynamically applied on the `Outlet` level.

### Changed
- `CreateOrderUseCase` enforces local assortment limits per outlet.
- `PricingService` updated to consider customized `Outlet` prices over global `Product` and `ModifierOption` defaults during calculations.

## [0.1.0] - 2026-03-17

### Added
- Core Domain Entities: `Company`, `Outlet`, `Product`, `Category`, `ModifierGroup`, `ModifierOption`.
- Initial Order mechanisms via `Order`, `Cart`, `OrderItem`, and `CreateOrderUseCase`.
- Order States and State Transitions processing via `ChangeOrderStatusUseCase` and Domain Events (`OrderCreatedEvent`, `OrderStatusChangedEvent`).
- Basic Loyalty functionality via `LoyaltyProfile`, points accrual, and deductions directly affecting order totals.
- Fundamental interfaces (`Repositories`, Base `Entity`, `Value Objects`).
