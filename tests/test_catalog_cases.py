import uuid
from unittest.mock import MagicMock

import pytest

from domain.entities.catalog import ModifierGroup
from domain.use_cases.catalog_cases import (
    ConfigureModifiersUseCase,
    ManageStopListUseCase,
)


@pytest.fixture
def outlet_repo_mock():
    return MagicMock()


@pytest.fixture
def product_repo_mock():
    return MagicMock()


def test_add_product_to_stop_list_success(outlet_repo_mock):
    use_case = ManageStopListUseCase(outlet_repo=outlet_repo_mock)
    outlet_id = uuid.uuid4()
    product_id = uuid.uuid4()

    outlet_mock = MagicMock()
    outlet_repo_mock.get_by_id.return_value = outlet_mock

    use_case.add_product_to_stop_list(outlet_id, product_id)

    outlet_repo_mock.get_by_id.assert_called_once_with(outlet_id)
    outlet_mock.add_to_product_stop_list.assert_called_once_with(product_id)
    outlet_repo_mock.save.assert_called_once_with(outlet_mock)


def test_add_product_to_stop_list_outlet_not_found(outlet_repo_mock):
    use_case = ManageStopListUseCase(outlet_repo=outlet_repo_mock)
    outlet_id = uuid.uuid4()
    product_id = uuid.uuid4()

    outlet_repo_mock.get_by_id.return_value = None

    use_case.add_product_to_stop_list(outlet_id, product_id)

    outlet_repo_mock.get_by_id.assert_called_once_with(outlet_id)
    outlet_repo_mock.save.assert_not_called()


def test_remove_product_from_stop_list_success(outlet_repo_mock):
    use_case = ManageStopListUseCase(outlet_repo=outlet_repo_mock)
    outlet_id = uuid.uuid4()
    product_id = uuid.uuid4()

    outlet_mock = MagicMock()
    outlet_repo_mock.get_by_id.return_value = outlet_mock

    use_case.remove_product_from_stop_list(outlet_id, product_id)

    outlet_repo_mock.get_by_id.assert_called_once_with(outlet_id)
    outlet_mock.remove_from_product_stop_list.assert_called_once_with(product_id)
    outlet_repo_mock.save.assert_called_once_with(outlet_mock)


def test_remove_product_from_stop_list_outlet_not_found(outlet_repo_mock):
    use_case = ManageStopListUseCase(outlet_repo=outlet_repo_mock)
    outlet_id = uuid.uuid4()
    product_id = uuid.uuid4()

    outlet_repo_mock.get_by_id.return_value = None

    use_case.remove_product_from_stop_list(outlet_id, product_id)

    outlet_repo_mock.get_by_id.assert_called_once_with(outlet_id)
    outlet_repo_mock.save.assert_not_called()


def test_add_modifier_group_success(product_repo_mock):
    use_case = ConfigureModifiersUseCase(product_repo=product_repo_mock)
    product_id = uuid.uuid4()

    modifier_group = MagicMock(spec=ModifierGroup)

    product_mock = MagicMock()
    product_mock.modifier_groups = []

    product_repo_mock.get_by_id.return_value = product_mock

    use_case.add_modifier_group(product_id, modifier_group)

    product_repo_mock.get_by_id.assert_called_once_with(product_id)
    assert modifier_group in product_mock.modifier_groups
    product_repo_mock.save.assert_called_once_with(product_mock)


def test_add_modifier_group_product_not_found(product_repo_mock):
    use_case = ConfigureModifiersUseCase(product_repo=product_repo_mock)
    product_id = uuid.uuid4()
    modifier_group = MagicMock(spec=ModifierGroup)

    product_repo_mock.get_by_id.return_value = None

    use_case.add_modifier_group(product_id, modifier_group)

    product_repo_mock.get_by_id.assert_called_once_with(product_id)
    product_repo_mock.save.assert_not_called()
