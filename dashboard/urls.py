from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardRouterView.as_view(), name='router'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/organizations/', views.ManageOrganizationsView.as_view(), name='manage_orgs'),
    path('admin/monitor/', views.GlobalMonitorView.as_view(), name='global_monitor'),
    path('admin/health/', views.SystemHealthView.as_view(), name='system_health'),
    path('citizen/', views.CitizenDashboardView.as_view(), name='citizen_dashboard'),
]
