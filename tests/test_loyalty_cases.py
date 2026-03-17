import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from domain.use_cases.loyalty_cases import CalculateAccrualUseCase
from domain.entities.client import LoyaltyProfile
from domain.entities.company import Company
from domain.entities.order import Order
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
    
    calculate_accrual_mock.assert_called_once_with(order_mock.total_amount, company_mock, spent_points=0)
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
