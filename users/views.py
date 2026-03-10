from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .forms import LoginForm, EventPlannerRegistrationForm
from events.models import Event, Report, Order, Ticket, CommissionRequest

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
    
    # Analytics: Total sales, total events, total tickets sold
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_events = Event.objects.count()
    total_tickets_sold = Ticket.objects.count()
    
    # Pending events for approval
    pending_events = Event.objects.filter(status='pending')
    
    approved_events_count = Event.objects.filter(status='approved').count()
    approved_events_list = Event.objects.filter(status='approved')

    # Reports
    reports = Report.objects.all()
    commission_requests = CommissionRequest.objects.all()
    
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
    commission_request = CommissionRequest.objects.get(id=request_id)
    commission_request.status = 'approved'
    commission_request.save()
    return redirect('admin_dashboard')

@login_required
def reject_payout(request, request_id):
    commission_request = CommissionRequest.objects.get(id=request_id)
    commission_request.status = 'rejected'
    commission_request.save()
    return redirect('admin_dashboard')

@login_required
def approve_event(request, event_id):
    if not request.user.is_superuser:
        return redirect('index')
    event = get_object_or_404(Event, id=event_id)
    event.status = 'approved'
    event.save()
    messages.success(request, f"Event '{event.title}' has been approved.")
    return redirect('admin_dashboard')

@login_required
def reject_event(request, event_id):
    if not request.user.is_superuser:
        return redirect('index')
    event = get_object_or_404(Event, id=event_id)
    event.status = 'rejected'
    event.save()
    messages.success(request, f"Event '{event.title}' has been rejected.")
    return redirect('admin_dashboard')
