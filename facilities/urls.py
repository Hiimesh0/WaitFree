from django.urls import path
from . import views

app_name = 'facilities'

urlpatterns = [
    # Branch management (branch role)
    path('branch/dashboard/', views.BranchDashboardView.as_view(), name='branch_dashboard'),
    path('branch/services/', views.ManageServicesView.as_view(), name='manage_services'),
    path('branch/counters/', views.ManageCountersView.as_view(), name='manage_counters'),
    path('branch/operators/', views.ManageOperatorsView.as_view(), name='manage_operators'),
    path('branch/monitor/', views.LiveQueueMonitorView.as_view(), name='live_monitor'),

    # Citizen-facing
    path('search/', views.FacilitySearchView.as_view(), name='facility_search'),
    path('<int:branch_id>/', views.BranchDetailView.as_view(), name='branch_detail'),
]
