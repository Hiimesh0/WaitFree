from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.UnifiedLoginView.as_view(), name='login'),
    path('otp/request/', views.CitizenOTPRequestView.as_view(), name='citizen_otp_request'),
    path('otp/verify/', views.CitizenOTPVerifyView.as_view(), name='citizen_otp_verify'),
    path('register/organization/', views.OrganizationRegisterView.as_view(), name='org_register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
