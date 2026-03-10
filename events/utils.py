import qrcode
import uuid
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Event, Order, Ticket
from django.utils import timezone
from datetime import timedelta

def get_categorized_events():
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=7)

    # Recently Added: created within the last 7 days
    recently_added = Event.objects.filter(created_at__gte=seven_days_ago)

    # Upcoming: start datetime is today or later, excluding recently added
    upcoming = Event.objects.filter(start_datetime__date__gte=today).exclude(id__in=recently_added)

    # Past: start datetime is before today, excluding recently added
    past = Event.objects.filter(start_datetime__date__lt=today).exclude(id__in=recently_added)

    return recently_added, upcoming, past


def process_order(request, cart, email, phone):
    order = Order.objects.create(email=email, phone=phone, total_amount=0)
    total_amount = 0
    attachments = []
    for event_id, quantity in cart.items():
        event = Event.objects.get(id=event_id)
        if event.available_tickets >= quantity:
            for _ in range(quantity):
                code = str(uuid.uuid4())
                ticket = Ticket.objects.create(event=event, order=order, code=code)
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(code)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')
                img_path = f'{settings.MEDIA_ROOT}/tickets/{ticket.id}.png'
                img.save(img_path)
                attachments.append(('ticket.png', open(img_path, 'rb').read(), 'image/png'))
            event.available_tickets -= quantity
            event.save()
            total_amount += event.price * quantity
    order.total_amount = total_amount
    order.save()
    email_msg = EmailMessage(
        'Your Tickets',
        'Please find your tickets attached.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    for attachment in attachments:
        email_msg.attach(*attachment)
    email_msg.send()