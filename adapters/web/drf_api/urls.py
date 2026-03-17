from django.urls import path

from .views import (
    CatalogConfigureModifiersView,
    CatalogOutletListView,
    CatalogStopListView,
    ExternalOrderAcceptView,
    LoyaltyCalculateAccrualView,
    OrderChangeStatusView,
    OrderCreateView,
    OrderProcessPaymentView,
)

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/status/', OrderChangeStatusView.as_view(), name='order-change-status'),
    path('orders/<str:order_id>/pay/', OrderProcessPaymentView.as_view(), name='order-process-payment'),

    path('catalog/outlets/<str:company_id>/', CatalogOutletListView.as_view(), name='catalog-outlets-list'),
    path('catalog/outlets/<str:outlet_id>/stop-list/', CatalogStopListView.as_view(), name='catalog-stoplist'),
    path('catalog/products/<str:product_id>/modifiers/', CatalogConfigureModifiersView.as_view(), name='catalog-configure-modifiers'),
    path('external-orders/', ExternalOrderAcceptView.as_view(), name='external-order-accept'),
    path('orders/<str:order_id>/accrue-loyalty/', LoyaltyCalculateAccrualView.as_view(), name='order-accrue-loyalty'),
]
