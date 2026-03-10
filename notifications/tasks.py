import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from events.models import NewsletterSubscriber, Event, Order, Ticket

logger = logging.getLogger(__name__)

@shared_task
def send_newsletter(subject, message):
    subscribers = NewsletterSubscriber.objects.all()
    for subscriber in subscribers:
        send_mail(
            subject,
            message,
            'from@example.com',
            [subscriber.email],
            fail_silently=False,
        )
        
@shared_task
def send_event_approval_notification(event_id, event_title):
    admins = User.objects.filter(is_superuser=True)
    admin_emails = [admin.email for admin in admins if admin.email]
    subject = f"New Event Pending Approval: {event_title}"
    message = f"A new event '{event_title}' (ID: {event_id}) is pending approval."
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=False,
    )

@shared_task
def send_report_notification(report_id, user_username, message):
    admins = User.objects.filter(is_superuser=True)
    admin_emails = [admin.email for admin in admins if admin.email]
    subject = f"New Issue Reported by {user_username}"
    message = f"User {user_username} reported an issue (Report ID: {report_id}): {message}"
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        fail_silently=False,
    )

@shared_task
def send_event_approval_request_email(event_id):
    try:
        event = Event.objects.get(id=event_id)
        admins = User.objects.filter(is_superuser=True)
        admin_emails = [admin.email for admin in admins if admin.email]

        if admin_emails:
            subject = f"New Event Submitted for Approval: {event.title}"
            message = f"""
            An event titled '{event.title}' has been submitted by {event.created_by.username}.

            Please review it in the admin dashboard: {settings.SITE_URL}/admin/events/event/{event.id}/change/

            Event Details:
            - Title: {event.title}
            - Description: {event.description}
            - Date: {event.date}
            - Time: {event.time}
            - Location: {event.location}
            - Price: ${event.price}
            - Available Tickets: {event.available_tickets}
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=False,
            )
            return f"Approval request email sent to admins for event {event_id}"
        return "No admins with emails found"
    except Event.DoesNotExist:
        return f"Event {event_id} not found"
    except Exception as e:
        return f"Failed to send approval request email for event {event_id}: {str(e)}"

@shared_task
def send_event_approval_status_email(event_id, status):
    try:
        event = Event.objects.get(id=event_id)
        event_planner_email = event.created_by.email

        subject = f"Your Event '{event.title}' Has Been {status.capitalize()}"
        message = f"""
        Dear {event.created_by.username},

        Your event '{event.title}' has been {status}.

        Event Details:
        - Title: {event.title}
        - Status: {status}

        Thank you for using Paperweight!
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [event_planner_email],
            fail_silently=False,
        )
        return f"Approval status email sent to {event_planner_email} for event {event_id}"
    except Event.DoesNotExist:
        return f"Event {event_id} not found"
    except Exception as e:
        return f"Failed to send approval status email for event {event_id}: {str(e)}"





@shared_task
def send_payment_confirmation(order_id, user_email):
    try:
        order = Order.objects.get(id=order_id)
        tickets = Ticket.objects.filter(order=order)

        subject = 'Payment Confirmation - Your Event Tickets'
        message = f"""
        Dear Customer,

        Thank you for your purchase! Your payment has been successfully processed.

        Order Details:
        - Order ID: {order.id}
        - Total Amount: ${order.total_amount:.2f}
        - Email: {order.email}
        - Phone: {order.phone}

        Tickets:
        """
        
        for ticket in tickets:
            message += f"\n- Event: {ticket.event.title}, Ticket Code: {ticket.code}, Status: {ticket.status}"

        message += "\n\nWe look forward to seeing you at the event!\nBest regards,\nThe Paperweight Team"

        email = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )

        for ticket in tickets:
            if ticket.qr_code:
                with ticket.qr_code.open('rb') as qr_file:
                    email.attach(f'qr_code_{ticket.code}.png', qr_file.read(), 'image/png')


        email.send(fail_silently=False)
        return f"Payment confirmation email sent to {user_email} for order {order_id}"
    except Order.DoesNotExist:
        return f"Order {order_id} not found"
    except Exception as e:
        return f"Failed to send email for order {order_id}: {str(e)}"

@shared_task
def cleanup_expired_orders():
    """
    Clean up pending and failed orders that have expired.
    Called periodically via Celery beat.
    """
    from django.utils import timezone
    
    expired_orders = Order.objects.filter(
        expires_at__lt=timezone.now(),
        payment_status__in=['pending', 'incomplete', 'failed']
    )
    
    count = 0
    for order in expired_orders:
        order.payment_status = 'expired'
        order.save()
        count += 1
        logger.info(f"Marked order {order.id} as expired")
    
    return f"Cleaned up {count} expired orders"

@shared_task
def retry_failed_payment(order_id):
    """
    Retry a failed payment. Can be called manually or via scheduler.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        if order.retry_count >= 3:
            logger.warning(f"Order {order_id} has exceeded max retry attempts (3)")
            return f"Order {order_id} has exceeded max retry attempts"
        
        if order.payment_status not in ['failed', 'incomplete']:
            return f"Order {order_id} is not in a retryable state (current: {order.payment_status})"
        
        # Increment retry count
        order.retry_count += 1
        order.payment_status = 'pending'
        order.save()
        
        logger.info(f"Retry attempt {order.retry_count} for order {order_id}")
        return f"Retry {order.retry_count}/3 initiated for order {order_id}"
        
    except Order.DoesNotExist:
        return f"Order {order_id} not found"
    except Exception as e:
        logger.error(f"Failed to retry payment for order {order_id}: {str(e)}")
        return f"Failed to retry payment: {str(e)}"