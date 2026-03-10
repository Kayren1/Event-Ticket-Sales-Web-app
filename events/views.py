from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import IntegrityError
from django.contrib.auth.models import User
from .models import NewsletterSubscriber, Event, Order, Ticket, Report, CommissionRequest
from decimal import Decimal
from .forms import EventForm, ReportForm
from .utils import process_order
from .utils import get_categorized_events
from notifications.tasks import send_event_approval_notification


def search(request):
    # Extract filter parameters from GET request
    categories = request.GET.get('categories', '').split(',')
    created_by = request.GET.get('created_by', '')

    # Start with all events
    events = Event.objects.all()

    # Apply category filter if provided
    if categories and categories != ['']:
        events = events.filter(category__in=categories)

    # Apply creator filter if provided
    if created_by:
        events = events.filter(created_by__username=created_by)

    # Prepare filter options for the template
    all_categories = Event.CATEGORIES
    all_creators = User.objects.filter(event__isnull=False).distinct().order_by('username')

    context = {
        'events': events,
        'selected_categories': categories if categories != [''] else [],
        'selected_creator': created_by,
        'all_categories': all_categories,
        'all_creators': all_creators,
    }

    return render(request, 'events/search.html', context)

def index(request):
    events = Event.objects.filter(status='approved')
    recently_added, upcoming, past = get_categorized_events()
    context = {
        'recently_added': recently_added,
        'upcoming': upcoming,
        'past': past,
    }
    return render(request, 'events/index.html', {'events': events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/event_detail.html', {'event': event})

def event_list(request):
    category = request.GET.get('category')
    if category:
        events = Event.objects.filter(category=category)
    else:
        events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

def add_to_cart(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[event_id] = cart.get(event_id, 0) + quantity
        request.session['cart'] = cart
        messages.success(request, f"Added {quantity} ticket(s) to cart.")
        return redirect('view_cart')
    return redirect('event_detail', event_id=event_id)

def buy_now(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[event_id] = quantity  # Override cart with just this item
        request.session['cart'] = cart
        return redirect('checkout')
    return redirect('event_detail', event_id=event_id)

def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    return JsonResponse({'count': count})

# cart/views.py
def view_cart(request):
    cart = request.session.get('cart', {})
    events = Event.objects.filter(id__in=cart.keys(), status='approved')
    cart_items = []
    total_amount = 0
    for event_id, quantity in cart.items():
        event = Event.objects.get(id=event_id)
        subtotal = event.price * quantity
        cart_items.append({
            'event': event,
            'quantity': quantity,
            'subtotal': subtotal
        })
        total_amount += subtotal
    return render(request, 'events/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

def clear_cart(request):
    if request.method == 'POST':
        if 'cart' in request.session:
            del request.session['cart']
            messages.success(request, 'Your cart has been cleared.')
        else:
            messages.info(request, 'Your cart is already empty.')
        return redirect('view_cart')
    return redirect('view_cart')

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.status = 'draft'
            # Set the date field based on the start_datetime field
            event.date = event.start_datetime.date()
            event.save()
            return redirect('pay_event_fee', event_id=event.id)  # Assumes 'pay_event_fee' in payments app
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})

@login_required
def event_fee_success(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if event.status == 'draft':
        event.status = 'pending'
        event.save()
        # Notify admins (using existing notification logic)
        from notifications.tasks import send_event_approval_notification
        send_event_approval_notification.delay(event.id, event.title)
    return redirect('eventplanner_dashboard')

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/edit_event.html', {'form': form, 'event': event})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.delete()
    return redirect('admin_dashboard')
    return render(request, 'events/delete_confirm.html', {'event': event})



@login_required
def eventplanner_dashboard(request):
    events = Event.objects.filter(created_by=request.user)
    approved_events_list = Event.objects.filter(status='approved')
    draft_events_list = Event.objects.filter(status='draft')
    for event in events:
        event.commission = Decimal(event.price) * Decimal(0.60)  # 60% commission

    context = {
        'events': events,
        'draft_events_list': draft_events_list,
        'approved_events_list': approved_events_list,
    }
    return render(request, 'events/eventplanner_dashboard.html', context)

@login_required
def report_issue(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, "Your report has been submitted.")
            return redirect('eventplanner_dashboard')
    else:
        form = ReportForm()
    return render(request, 'events/report_issue.html', {'form': form})

#@login_required
def verify_ticket(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            ticket = Ticket.objects.get(code=code)
            if ticket.status == 'valid' and ticket.event.date >= timezone.now().date():
                ticket.status = 'used'
                ticket.used_at = timezone.now()
                ticket.save()
                messages.success(request, "Ticket is valid and has been used.")
            elif ticket.status == 'used':
                messages.warning(request, "Ticket has already been used.")
            elif ticket.event.date < timezone.now().date():
                messages.warning(request, "Ticket is expired.")
            else:
                messages.warning(request, "Ticket is invalid.")
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket code.")
        return redirect('verify_ticket')
    return render(request, 'events/verify_ticket.html')

def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            if email:
                NewsletterSubscriber.objects.create(email=email)
                messages.success(request, "Thank you for subscribing to our newsletter!")
            else:
                messages.error(request, "Please provide a valid email address.")
            messages.success(request, "Thank you for subscribing to our newsletter!")
        except IntegrityError:
            messages.warning(request, "This email is already subscribed.")
    messages.error(request, "Invalid request method. Please use the form to subscribe.")
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
