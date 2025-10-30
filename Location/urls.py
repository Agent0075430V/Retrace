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

urlpatterns = [
    path('locations/', views.location_list, name='location_list'),
    path('locations/<int:pk>/', views.location_detail, name='location-detail'),
    path('locations/create/', views.location_create, name='location-create'),
    path('locations/<int:pk>/update/', views.location_update, name='location-update'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location-delete'),
    path('locations/<int:pk>/settings/', views.location_settings, name='location-settings-update'),
    # path('locations/<int:pk>/reports/', views.location_report, name='location-reports'),  # Removed duplicate/conflicting route
]