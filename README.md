# Clean Architecture Platform Demo
This project demonstrates a restaurant platform implementing Clean Architecture principles in Python. It is divided into a pure business logic **Domain** layer and a framework-dependent **Infrastructure** layer (Adapters).

## Project Structure
The codebase follows the hexagonal architecture (Ports & Adapters) pattern:

- **`domain/`**: Core business rules (Pure Python, zero dependencies).
  - `entities/`: Core aggregates (Cart, Client, Company, Orders).
  - `use_cases/`: Business operations (Create Order, Process Payment).
  - `interfaces/`: Abstract ports (Gateways, Repositories).
  - `services/`: Computational logic (Pricing, Delivery).
- **`adapters/`**: Framework-specific implementations.
  - `db/django_orm/`: Persistent storage using Django ORM.
  - `web/drf_api/`: HTTP API layer using Django REST Framework.
- **`config/`**: Composition root and system configuration.
  - `di.py`: Dependency Injection container wiring domain with adapters.
  - `settings.py`: Django configuration.

## Key Features
- **Strict Isolation**: The domain layer has no knowledge of Django or the database.
- **Framework Agnostic**: The web and DB layers are isolated in `adapters/`, making it easy to swap them for FastAPI or SQLAlchemy.
- **Advanced Pricing**: Supports outlet-specific price overrides and complex modifier rules.
- **Unified CRUD Engine**: Standardized Create, Read, Update, Delete, and List operations for all primary entities (`Client`, `Company`, `Outlet`, `Product`).
- **Generic Architecture**: Utilizes a highly reusable generic CRUD layer (`CrudUseCase`, `CrudViewSet`) that minimizes boilerplate while enforcing strict domain isolation.
- **Modifier Management**: API endpoints for dynamic configuration of product modifiers.
- **Loyalty System**: Multi-tier loyalty levels based on historical customer spend, with dedicated accrual calculation endpoints.
- **External Integrations**: Support for accepting and processing orders from third-party platforms.
- **Automated Workflows**: Automatic courier Dispatching, Receipt generation, and Status transitions.

## Running and Testing
The project uses `uv` for dependency management.

### Installation
```bash
uv pip install -e .
```

### Run Tests
- **Unit Tests (Domain)**: `uv run pytest tests/test_order_cases.py`
- **Integration Tests (Adapters)**: `uv run pytest tests/adapters/`

To run all tests:
```bash
uv run pytest
```

### Static Analysis and Linting
The project maintains high code quality using `ruff` and `pyright`.
```bash
# Run linter
uv run ruff check .

# Run static analyzer
uv run pyright .
```
