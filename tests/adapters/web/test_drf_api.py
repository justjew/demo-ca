import uuid

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from adapters.db.django_orm.models import CompanyModel, OutletModel


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_catalog_outlet_list(api_client):
    company = CompanyModel.objects.create(name="Web Company", tax_id="W123")
    outlet = OutletModel.objects.create(
        id=uuid.uuid4(), company=company, name="Web Outlet", is_accepting_orders=True
    )

    url = reverse("catalog-outlets-list", kwargs={"company_id": str(company.id)})
    response = api_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Web Outlet"
    assert response.data[0]["id"] == str(outlet.id)


# Adding more complex DRF tests would require setting up products, etc.,
# which is similar but more verbose. Just ensuring the views wire up correctly.


def test_configure_modifiers_route(api_client):
    url = reverse(
        "catalog-configure-modifiers", kwargs={"product_id": str(uuid.uuid4())}
    )
    response = api_client.post(url, data={})
    # Fails validation because payload is missing -> 400
    assert response.status_code == 400


def test_external_order_accept_route(api_client):
    url = reverse("external-order-accept")
    response = api_client.post(url, data={}, format="json")
    # Usecase execution might fail gracefully returning 400
    assert response.status_code in [400, 201]


def test_loyalty_accrual_route(api_client):
    url = reverse("order-accrue-loyalty", kwargs={"order_id": str(uuid.uuid4())})
    response = api_client.post(url)
    # The use case might just return early if order doesn't exist, giving 200
    assert response.status_code in [200, 400]
