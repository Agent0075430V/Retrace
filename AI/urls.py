from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import LostProductViewSet, FoundProductViewSet, MatchResultViewSet, NotificationViewSet, RouteMapViewSet

router = DefaultRouter()
router.register(r'lost', LostProductViewSet, basename='lost')
router.register(r'found', FoundProductViewSet, basename='found')
router.register(r'matches', MatchResultViewSet, basename='matches')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'routes', RouteMapViewSet, basename='routes')

urlpatterns = [
    path('api/ai/', include(router.urls)),
    path('home/', views.home, name='home'),
    path('', views.home, name='home'),
    path('search/', views.search_items, name='search_items'),
    path('report-lost/', views.report_lost_product, name='report_lost'),
    path('report-found/', views.report_found_product, name='report_found'),
    path('add_found_product/', views.add_found_product, name='add_found_product'),
    path('add_lost_product/', views.add_lost_product, name='add_lost_product'),
    path('mark-found/<int:lost_item_id>/', views.mark_item_as_found, name='mark_item_as_found'),
    path('mark-found-form/<int:lost_item_id>/', views.get_mark_found_form, name='get_mark_found_form'),
    path('claim-item/<int:lost_item_id>/', views.claim_item, name='claim_item'),
    path('claim-form/<int:lost_item_id>/', views.get_claim_form, name='get_claim_form'),
    path('verify-claim/<int:claim_id>/', views.verify_claim, name='verify_claim'),
    path('all-lost-items/', views.all_lost_items, name='all_lost_items'),
    path('all-found-items/', views.all_found_items, name='all_found_items'),
    path('all-claimed-items/', views.all_claimed_items, name='all_claimed_items'),
]
