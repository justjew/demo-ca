import pytest
from django.urls import reverse
from rest_framework.test import APIClient
import uuid

from adapters.db.django_orm.models import CompanyModel, OutletModel

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_catalog_outlet_list(api_client):
    company = CompanyModel.objects.create(name="Web Company", tax_id="W123")
    outlet = OutletModel.objects.create(
        id=uuid.uuid4(),
        company=company,
        name="Web Outlet",
        is_accepting_orders=True
    )
    
    url = reverse('catalog-outlets-list', kwargs={'company_id': str(company.id)})
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == "Web Outlet"
    assert response.data[0]['id'] == str(outlet.id)

# Adding more complex DRF tests would require setting up products, etc.,
# which is similar but more verbose. Just ensuring the views wire up correctly.
