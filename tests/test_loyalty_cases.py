import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from domain.entities.client import LoyaltyProfile
from domain.entities.company import Company
from domain.entities.order import Order
from domain.use_cases.loyalty_cases import CalculateAccrualUseCase
from domain.value_objects import Money


@pytest.fixture
def order_repo_mock():
    return MagicMock()

@pytest.fixture
def client_repo_mock():
    return MagicMock()

@pytest.fixture
def company_repo_mock():
    return MagicMock()

@pytest.fixture
def event_dispatcher_mock():
    return MagicMock()

@pytest.fixture
def use_case(order_repo_mock, client_repo_mock, company_repo_mock, event_dispatcher_mock):
    return CalculateAccrualUseCase(
        order_repo=order_repo_mock,
        client_repo=client_repo_mock,
        company_repo=company_repo_mock,
        event_dispatcher=event_dispatcher_mock
    )

def test_calculate_accrual_order_not_found(use_case, order_repo_mock):
    order_id = uuid.uuid4()
    order_repo_mock.get_by_id.return_value = None

    use_case.execute(order_id, datetime.now())

    order_repo_mock.get_by_id.assert_called_once_with(order_id)
    use_case.client_repo.get_loyalty_profile.assert_not_called()

def test_calculate_accrual_guest_checkout(use_case, order_repo_mock):
    order_id = uuid.uuid4()
    order_mock = MagicMock(spec=Order)
    order_mock.client_id = None
    order_repo_mock.get_by_id.return_value = order_mock

    use_case.execute(order_id, datetime.now())

    use_case.client_repo.get_loyalty_profile.assert_not_called()

def test_calculate_accrual_profile_not_found(use_case, order_repo_mock, client_repo_mock):
    order_id = uuid.uuid4()
    order_mock = MagicMock(spec=Order)
    order_mock.client_id = uuid.uuid4()
    order_mock.outlet_id = uuid.uuid4()
    order_repo_mock.get_by_id.return_value = order_mock

    client_repo_mock.get_loyalty_profile.return_value = None

    use_case.execute(order_id, datetime.now())

    client_repo_mock.get_loyalty_profile.assert_called_once_with(order_mock.client_id, order_mock.outlet_id)
    use_case.company_repo.get_by_id.assert_not_called()

def test_calculate_accrual_company_not_found(use_case, order_repo_mock, client_repo_mock, company_repo_mock):
    order_id = uuid.uuid4()
    order_mock = MagicMock(spec=Order)
    order_mock.client_id = uuid.uuid4()
    order_mock.outlet_id = uuid.uuid4()
    order_repo_mock.get_by_id.return_value = order_mock

    profile_mock = MagicMock(spec=LoyaltyProfile)
    profile_mock.company_id = uuid.uuid4()
    client_repo_mock.get_loyalty_profile.return_value = profile_mock

    company_repo_mock.get_by_id.return_value = None

    use_case.execute(order_id, datetime.now())

    company_repo_mock.get_by_id.assert_called_once_with(profile_mock.company_id)
    use_case.event_dispatcher.assert_not_called()

def test_calculate_accrual_no_total_amount(use_case, order_repo_mock, client_repo_mock, company_repo_mock):
    order_id = uuid.uuid4()
    order_mock = MagicMock(spec=Order)
    order_mock.client_id = uuid.uuid4()
    order_mock.outlet_id = uuid.uuid4()
    order_mock.total_amount = None
    order_repo_mock.get_by_id.return_value = order_mock

    profile_mock = MagicMock(spec=LoyaltyProfile)
    profile_mock.company_id = uuid.uuid4()
    client_repo_mock.get_loyalty_profile.return_value = profile_mock

    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock

    use_case.execute(order_id, datetime.now())
    use_case.event_dispatcher.assert_not_called()

def test_calculate_accrual_success(use_case, order_repo_mock, client_repo_mock, company_repo_mock, event_dispatcher_mock, monkeypatch):
    order_id = uuid.uuid4()
    current_dt = datetime.now()

    order_mock = MagicMock(spec=Order)
    order_mock.id = order_id
    order_mock.client_id = uuid.uuid4()
    order_mock.outlet_id = uuid.uuid4()
    order_mock.total_amount = MagicMock(spec=Money)
    order_mock.total_amount.amount = 1000
    order_repo_mock.get_by_id.return_value = order_mock

    profile_mock = MagicMock(spec=LoyaltyProfile)
    profile_mock.company_id = uuid.uuid4()
    profile_mock.total_spent = 500
    client_repo_mock.get_loyalty_profile.return_value = profile_mock

    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock

    # Mocking static method LoyaltyService.calculate_accrual
    calculate_accrual_mock = MagicMock(return_value=100)
    monkeypatch.setattr('domain.services.loyalty_service.LoyaltyService.calculate_accrual', calculate_accrual_mock)

    use_case.execute(order_id, current_dt)

    calculate_accrual_mock.assert_called_once_with(order_mock.total_amount, company_mock, total_spent=500, spent_points=0)
    profile_mock.add_points.assert_called_once_with(100)
    assert profile_mock.total_spent == 1500  # 500 + 1000
    client_repo_mock.save_loyalty_profile.assert_called_once_with(profile_mock)

    event_dispatcher_mock.assert_called_once()
    event = event_dispatcher_mock.call_args[0][0]
    assert event.client_id == order_mock.client_id
    assert event.points_added == 100
    assert event.order_id == order_id

def test_calculate_accrual_no_points_added(use_case, order_repo_mock, client_repo_mock, company_repo_mock, event_dispatcher_mock, monkeypatch):
    order_id = uuid.uuid4()
    current_dt = datetime.now()

    order_mock = MagicMock(spec=Order)
    order_mock.client_id = uuid.uuid4()
    order_mock.outlet_id = uuid.uuid4()
    order_mock.total_amount = MagicMock(spec=Money)
    order_repo_mock.get_by_id.return_value = order_mock

    profile_mock = MagicMock(spec=LoyaltyProfile)
    profile_mock.company_id = uuid.uuid4()
    client_repo_mock.get_loyalty_profile.return_value = profile_mock

    company_mock = MagicMock(spec=Company)
    company_repo_mock.get_by_id.return_value = company_mock

    calculate_accrual_mock = MagicMock(return_value=0)
    monkeypatch.setattr('domain.services.loyalty_service.LoyaltyService.calculate_accrual', calculate_accrual_mock)

    use_case.execute(order_id, current_dt)

    profile_mock.add_points.assert_not_called()
    client_repo_mock.save_loyalty_profile.assert_not_called()
    event_dispatcher_mock.assert_not_called()


def test_company_get_loyalty_accrual_rate_for_spent():
    from domain.entities.company import Company, LoyaltyLevel

    # 1. Fallback behavior (no levels configured)
    company_no_levels = Company(name="Test", tax_id="123")
    assert company_no_levels.get_loyalty_accrual_rate_for_spent(0) == 0.05
    assert company_no_levels.get_loyalty_accrual_rate_for_spent(1000) == 0.05

    # 2. Configured levels
    levels = [
        LoyaltyLevel(name="Bronze", min_spent_amount=0, accrual_rate=0.05),
        LoyaltyLevel(name="Silver", min_spent_amount=10000, accrual_rate=0.10),
        LoyaltyLevel(name="Gold", min_spent_amount=50000, accrual_rate=0.15)
    ]
    company = Company(name="Test", tax_id="123", loyalty_levels=levels)

    # 0 -> Bronze (5%)
    assert company.get_loyalty_accrual_rate_for_spent(0) == 0.05
    # 5000 -> Bronze (5%)
    assert company.get_loyalty_accrual_rate_for_spent(5000) == 0.05
    # 10000 -> Silver (10%)
    assert company.get_loyalty_accrual_rate_for_spent(10000) == 0.10
    # 49999 -> Silver (10%)
    assert company.get_loyalty_accrual_rate_for_spent(49999) == 0.10
    # 50000 -> Gold (15%)
    assert company.get_loyalty_accrual_rate_for_spent(50000) == 0.15
    # 1000000 -> Gold (15%)
    assert company.get_loyalty_accrual_rate_for_spent(1000000) == 0.15


def test_loyalty_service_calculate_accrual():
    from domain.entities.company import Company, LoyaltyLevel
    from domain.services.loyalty_service import LoyaltyService
    from domain.value_objects import Money

    levels = [
        LoyaltyLevel(name="Silver", min_spent_amount=10000, accrual_rate=0.10),
    ]
    company = Company(name="Test", tax_id="123", loyalty_levels=levels)

    # Customer with 15000 total spent (Silver, 10%)
    # Order for 2000 money units, paying 500 with points
    # Accrual should be on (2000 - 500) = 1500 amount
    # Rate is 0.10, so 1500 * 0.10 = 150 points

    order_total = Money(amount=2000, currency="USD")
    points = LoyaltyService.calculate_accrual(order_total, company, total_spent=15000, spent_points=500)
    assert points == 150

