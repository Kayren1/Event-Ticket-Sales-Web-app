from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_event_planner, name='register'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('submit_payout/<int:event_id>/', views.submit_payout, name='submit_payout'),
    path('approve_payout/<int:request_id>/', views.approve_payout, name='approve_payout'),
    path('reject_payout/<int:request_id>/', views.reject_payout, name='reject_payout'),
    path('approve_event/<int:event_id>/', views.approve_event, name='approve_event'),
    path('reject_event/<int:event_id>/', views.reject_event, name='reject_event'),
]