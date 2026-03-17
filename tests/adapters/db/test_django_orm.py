import uuid

import pytest

from adapters.db.django_orm.models import CompanyModel
from adapters.db.django_orm.repositories import (
    DjangoClientRepository,
    DjangoCompanyRepository,
    DjangoOutletRepository,
)
from domain.entities.client import Client
from domain.entities.company import Company
from domain.entities.outlet import Outlet


@pytest.mark.django_db
def test_company_repository_save_and_get():
    repo = DjangoCompanyRepository()

    company_id = uuid.uuid4()
    company = Company(
        id=company_id,
        name="Test Company",
        tax_id="12345678"
    )

    # Save
    repo.save(company)

    # Verify DB
    model = CompanyModel.objects.get(id=company_id)
    assert model.name == "Test Company"

    # Get
    fetched = repo.get_by_id(company_id)
    assert fetched is not None
    assert fetched.name == "Test Company"
    assert fetched.tax_id == "12345678"


@pytest.mark.django_db
def test_client_repository_save_and_get():
    repo = DjangoClientRepository()

    client_id = uuid.uuid4()
    client = Client(
        id=client_id,
        phone_number="+1234567890",
        first_name="Ivan",
        last_name="Ivanov"
    )

    repo.save_client(client)

    fetched = repo.get_by_phone("+1234567890")
    assert fetched is not None
    assert fetched.id == client_id
    assert fetched.first_name == "Ivan"


@pytest.mark.django_db
def test_outlet_repository_save_and_get():
    company = CompanyModel.objects.create(name="C1", tax_id="111")
    repo = DjangoOutletRepository()

    outlet_id = uuid.uuid4()
    outlet = Outlet(
        id=outlet_id,
        company_id=company.id,
        name="Main Outlet",
        is_accepting_orders=True
    )

    repo.save(outlet)

    fetched = repo.get_by_id(outlet_id)
    assert fetched is not None
    assert fetched.name == "Main Outlet"

    lst = repo.list_by_company(company.id)
    assert len(lst) == 1
    assert lst[0].id == outlet_id
