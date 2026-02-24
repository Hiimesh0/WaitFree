from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('dashboard/', views.OrganizationDashboardView.as_view(), name='dashboard'),
    path('branches/register/', views.RegisterBranchView.as_view(), name='register_branch'),
    path('branches/performance/', views.BranchPerformanceView.as_view(), name='branch_performance'),
]
