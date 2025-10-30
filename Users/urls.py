from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .import views
from .api_views import RegisterView, CustomObtainAuthToken, ProfileUserViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileUserViewSet, basename='profileuser')
router.register(r'userprofiles', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', CustomObtainAuthToken.as_view(), name='token'),
    path('login/', views.Login, name='login'),
    path('logout/', views.Logout, name='logout'),
    path('dashboard/', views.Dashboard, name='dashboard'),
    path('signup/', views.Register, name='register'),
    path('forgot-password/', views.ForgotPassword, name='forgot_password'),
    path('verify-otp/', views.VerifyOTP, name='verify_otp'),
    path('resend-otp/', views.ResendOTP, name='resend_otp'),
    path('reset-password/', views.ResetPassword, name='reset_password'),
    path('profile/', views.UserProfile, name='profile'),
    path('settings/', views.UserSettings, name='user_settings'),
    path('location-settings/', views.UserLocationSettings, name='user_location_settings'),
    path('about/', views.About, name='about'),
    path('contact/', views.Contact, name='contact'),
    path('', include(router.urls)),
]
