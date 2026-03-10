import logging
import stripe
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from events.utils import process_order  # Assuming this function exists in events app
from events.models import CreationFeePayment, Event, Order, Ticket  # Assuming Event model exists
from django.contrib import messages
from notifications.tasks import send_payment_confirmation

stripe.api_key = settings.STRIPE_SECRET_KEY



def calculate_total(cart):
    total = 0
    for event_id, quantity in cart.items():
        try:
            event = Event.objects.get(id=int(event_id))  # Convert string event_id to int
            total += event.price * quantity  # price (Decimal) * quantity (int)
        except Event.DoesNotExist:
            # Handle missing events (e.g., log error or skip)
            continue
    return total

# payments/views.py
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('index')

    total_amount = calculate_total(cart)
    cart_items = []
    for event_id, quantity in cart.items():
        try:
            event = Event.objects.get(id=int(event_id))
            cart_items.append({
                'event': event,
                'quantity': quantity,
                'subtotal': event.price * quantity
            })
        except Event.DoesNotExist:
            continue
    if event.available_tickets < quantity:
            messages.error(request, f"Not enough tickets left for {event.title}.")
            return redirect('cart')
    # Create PaymentIntent on initial load (GET request)
    payment_intent = None
    order = None
    if 'order_id' in request.session:
        order = get_object_or_404(Order, id=request.session['order_id'])
        if order.payment_status in ['incomplete', 'failed']:
            payment_intent = stripe.PaymentIntent.retrieve(order.payment_intent_id)
        elif order.payment_status == 'completed':
            return redirect('payment_success')

    if not payment_intent:
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),
                currency='usd',
                description='Event Ticket Purchase',
            )
        except stripe.error.StripeError as e:
            messages.error(request, f"Payment setup failed: {str(e)}")
            return render(request, 'payments/checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'error': str(e)
            })

    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        # Orders expire after 24 hours if not completed
        expires_at = timezone.now() + timedelta(hours=24)
        order = Order.objects.create(
            email=email,
            phone=phone,
            total_amount=total_amount,
            payment_status='pending',
            payment_intent_id=payment_intent.id,  # Store the PaymentIntent ID
            expires_at=expires_at
        )
        request.session['order_id'] = order.id
        request.session.save()  # Explicitly save session

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'order': order,
        'client_secret': payment_intent.client_secret,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payments/checkout.html', context)

# payments/views.py
@login_required
def process_creation_fee_payment(request):
    if request.method == 'POST':
        order_id = request.session.get('order_id')
        if not order_id:
            messages.error(request, 'Order not found. Please try again.')
            return redirect('event_detail', event_id=request.POST.get('event_id'))

        order = get_object_or_404(CreationFeePayment, id=order_id)
        event = order.event

        try:
            payment_intent = stripe.PaymentIntent.retrieve(order.payment_intent_id)
            if payment_intent.status == 'succeeded':
                order.payment_status = 'completed'
                order.save()
                event.status = 'pending'
                event.save()
                from notifications.tasks import send_event_approval_notification
                send_event_approval_notification.delay(event.id, event.title)
                messages.success(request, 'Payment successful! Your event is now pending approval.')
                return redirect('eventplanner_dashboard')

            elif payment_intent.status == 'requires_action':
                order.payment_status = 'incomplete'
                order.save()
                messages.warning(request, 'Additional action required to complete payment.')
                return render(request, 'payments/pay_event_fee.html', {
                    'event': event,
                    'creation_fee': order.total_amount,
                    'order': order,
                    'client_secret': payment_intent.client_secret,
                    'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
                    'error': 'Please complete the payment authentication.'
                })

            else:
                order.payment_status = 'failed'
                order.save()
                messages.error(request, 'Payment failed. Please try again.')
                return render(request, 'payments/pay_event_fee.html', {
                    'event': event,
                    'creation_fee': order.total_amount,
                    'order': order,
                    'error': 'Payment failed. Please try again.',
                    'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
                })

        except stripe.error.StripeError as e:
            order.payment_status = 'failed'
            order.save()
            messages.error(request, f"Payment failed: {str(e)}")
            return render(request, 'payments/pay_event_fee.html', {
                'event': event,
                'creation_fee': order.total_amount,
                'order': order,
                'error': str(e),
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            })

    return redirect('event_detail', event_id=request.POST.get('event_id'))

# payments/views.py
def process_payment(request):
    if request.method == 'POST':
        order_id = request.session.get('order_id')
        if not order_id:
            messages.error(request, 'Order not found. Please try again.')
            return redirect('checkout')

        order = get_object_or_404(Order, id=order_id)
        cart = request.session.get('cart', {})

        try:
            # Mark payment as completed and create tickets
            order.payment_status = 'completed'
            order.save()

            # Create tickets for each item in cart
            for event_id, quantity in cart.items():
                event = Event.objects.get(id=int(event_id))
                for _ in range(quantity):
                    ticket = Ticket.objects.create(
                        event=event,
                        order=order,
                        code=f'TICKET-{order.id}-{event_id}',
                        status='valid',
                    )
                event.available_tickets -= quantity
                event.save()

            request.session['last_order_id'] = order.id
            request.session['cart'] = {}
            send_payment_confirmation.delay(order.id, order.email)
            messages.success(request, 'Payment successful! Your tickets have been generated.')
            return redirect('payment_success')

        except Exception as e:
            order.payment_status = 'failed'
            order.save()
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('checkout')

    return redirect('checkout')

logger = logging.getLogger(__name__)

def payment_success(request):
    order_id = request.session.get('last_order_id')
    if not order_id:
        messages.error(request, 'No order found. Please try again.')
        return redirect('checkout')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found. Please contact support.')
        return redirect('index')

    if order.payment_status != 'completed':
        messages.error(request, 'Payment not completed. Please try again or contact support.')
        return redirect('checkout')

    # Log the successful payment
    logger.info(f"Payment completed for order {order.id} by {order.email}")

    # Clear the cart
    request.session['cart'] = {}

    # Update ticket availability and generate tickets
    for ticket in order.ticket_set.all():  # Loop through each ticket in the order
        event = ticket.event  # Get the event tied to the ticket
        event.available_tickets = F('available_tickets') - 1  # Atomic update
        event.save()
        event.refresh_from_db()  # Ensure the latest value is loaded
    # Send confirmation email
    send_payment_confirmation.delay(order.id, order.email)

    # Prepare context for the success page
    context = {
        'order': order,
        'ticket_url': reverse('view_cart'),
    }

    messages.success(request, 'Payment successful! Your tickets have been generated.')
    return render(request, 'payments/success.html', context)

@login_required
def pay_event_fee(request, event_id):
    # Retrieve the event and verify ownership and status
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if event.status != 'draft':
        messages.error(request, "This event is not in draft status.")
        return redirect('event_detail', event_id=event.id)

    # Set the fixed creation fee (e.g., $10.00)
    creation_fee = 10.00

    # Get or create a payment record
    payment, created = CreationFeePayment.objects.get_or_create(
        event=event,
        defaults={'amount': creation_fee, 'status': 'pending'}
    )

    if created or payment.status == 'pending':
        try:
            # Create or retrieve the PaymentIntent
            if not payment.payment_intent_id:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(creation_fee * 100),  # Convert to cents
                    currency='usd',
                    description=f'Creation Fee for {event.title}',
                    metadata={'event_id': event.id},
                )
                payment.payment_intent_id = payment_intent.id
                payment.save()
            else:
                payment_intent = stripe.PaymentIntent.retrieve(payment.payment_intent_id)

            # Context for the payment form
            context = {
                'event': event,
                'creation_fee': creation_fee,
                'client_secret': payment_intent.client_secret,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            }
            return render(request, 'payments/pay_event_fee.html', context)
        except stripe.error.StripeError as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f"Payment setup failed: {str(e)}")
            return render(request, 'payments/pay_event_fee.html', {'event': event, 'error': str(e)})

    elif payment.status == 'completed':
        messages.info(request, "The creation fee has already been paid.")
        return redirect('event_detail', event_id=event.id)

    else:  # payment.status == 'failed'
        messages.error(request, "Payment failed previously. Please try again.")
        return render(request, 'payments/pay_event_fee.html', {'event': event, 'error': "Previous payment failed."})


# Stripe Webhook Handler
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events for payment status updates.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle payment_intent events
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'completed'
            order.save()
            logger.info(f"Webhook: Order {order.id} marked as completed")
        except Order.DoesNotExist:
            logger.warning(f"Webhook: Order not found for payment intent {payment_intent.id}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'failed'
            order.save()
            logger.warning(f"Webhook: Order {order.id} marked as failed")
            # Optionally retry the payment
            from notifications.tasks import retry_failed_payment
            retry_failed_payment.delay(order.id)
        except Order.DoesNotExist:
            logger.warning(f"Webhook: Order not found for payment intent {payment_intent.id}")
    
    return JsonResponse({'status': 'success'})
