import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal
from .forms import LoginForm, EventPlannerRegistrationForm
from events.models import Event, Report, Order, Ticket, CommissionRequest

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('eventplanner_dashboard')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')


def register_event_planner(request):
    if request.method == 'POST':
        form = EventPlannerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = EventPlannerRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    
    from django.core.paginator import Paginator
    
    # Analytics: Total sales, total events, total tickets sold
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_events = Event.objects.count()
    total_tickets_sold = Ticket.objects.count()
    
    # Pending events for approval
    pending_events = Event.objects.filter(status='pending')
    
    approved_events_count = Event.objects.filter(status='approved').count()
    approved_events_list = Event.objects.filter(status='approved')

    # Add pagination for Reports and CommissionRequests
    reports_list = Report.objects.all().order_by('-created_at')
    commission_requests_list = CommissionRequest.objects.all().order_by('-created_at')
    
    # Paginate reports (50 per page)
    reports_paginator = Paginator(reports_list, 50)
    reports_page = request.GET.get('reports_page', 1)
    reports = reports_paginator.get_page(reports_page)
    
    # Paginate commission requests (50 per page)
    commission_paginator = Paginator(commission_requests_list, 50)
    commission_page = request.GET.get('commission_page', 1)
    commission_requests = commission_paginator.get_page(commission_page)
    
    context = {
        'total_sales': total_sales,
        'total_events': total_events,
        'total_tickets_sold': total_tickets_sold,
        'approved_events': approved_events_count,
        'approved_events_list': approved_events_list,
        'pending_events': pending_events,
        'reports': reports,
        'commission_requests': commission_requests,
    }
    return render(request, 'users/admin.html', context)

@login_required
def submit_payout(request, event_id):
    event = Event.objects.get(id=event_id, created_by=request.user)
    commission = Decimal(event.price) * Decimal(0.60)
    CommissionRequest.objects.create(
        event=event,
        planner=request.user,
        commission_amount=commission
    )
    return redirect('eventplanner_dashboard')

@login_required
def approve_payout(request, request_id):
    # Check if user is superuser (permission check)
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to approve payouts.')
        return redirect('index')
    
    commission_request = CommissionRequest.objects.get(id=request_id)
    commission_request.status = 'approved'
    commission_request.save()
    messages.success(request, 'Payout approved successfully.')
    return redirect('admin_dashboard')

@login_required
def reject_payout(request, request_id):
    # Check if user is superuser (permission check)
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to reject payouts.')
        return redirect('index')
    
    commission_request = CommissionRequest.objects.get(id=request_id)
    commission_request.status = 'rejected'
    commission_request.save()
    messages.success(request, 'Payout rejected successfully.')
    return redirect('admin_dashboard')

@login_required
def approve_event(request, event_id):
    if not request.user.is_superuser:
        return redirect('index')
    try:
        event = get_object_or_404(Event, id=event_id)
        event.status = 'approved'
        event.save()
        logger.info(f"Event {event.id} approved by {request.user.username}")
        messages.success(request, f"Event '{event.title}' has been approved.")
    except Exception as e:
        logger.error(f"Error approving event {event_id}: {str(e)}")
        messages.error(request, 'Error approving event.') 
    return redirect('admin_dashboard')

@login_required
def reject_event(request, event_id):
    if not request.user.is_superuser:
        return redirect('index')
    try:
        event = get_object_or_404(Event, id=event_id)
        event.status = 'rejected'
        event.save()
        logger.info(f"Event {event.id} rejected by {request.user.username}")
        messages.success(request, f"Event '{event.title}' has been rejected.")
    except Exception as e:
        logger.error(f"Error rejecting event {event_id}: {str(e)}")
        messages.error(request, 'Error rejecting event.')
    return redirect('admin_dashboard')
