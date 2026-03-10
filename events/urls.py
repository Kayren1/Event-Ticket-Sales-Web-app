from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/', views.event_list, name='event_list'),
    path('event/<int:event_id>/fee-success/', views.event_fee_success, name='event_fee_success'),
    path('event/<int:event_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('event/<int:event_id>/buy-now/', views.buy_now, name='buy_now'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('create_event/', views.create_event, name='create_event'),
    path('eventplanner/', views.eventplanner_dashboard, name='eventplanner_dashboard'),
    path('report_issue/', views.report_issue, name='report_issue'),
    path('verify_ticket/', views.verify_ticket, name='verify_ticket'),
    path('subscribe_newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    
]