"""
URL configuration for Retrace project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

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
     path('Lost_product/', views.report_lost, name='lost_product'),
    path('found/', views.report_found, name='found_product'),
    path('Dashboard/', views.Product, name='Dashboard'),
    path('api/ai/', include(router.urls))
]
