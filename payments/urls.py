from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('pay_event_fee/<int:event_id>/', views.pay_event_fee, name='pay_event_fee'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('process-creation-fee-payment/', views.process_creation_fee_payment, name='process_creation_fee_payment'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]