# Quick Reference - Celery Implementation

## 🚀 Start Everything (Windows)
```bash
start_dev.bat
```
Opens 3 windows: Django, Celery Worker, Celery Beat

## 🚀 Start Everything (Mac/Linux)
```bash
# Terminal 1
redis-server

# Terminal 2
python manage.py runserver

# Terminal 3
celery -A paperweight worker -l info

# Terminal 4
celery -A paperweight beat -l info
```

## ✅ Verify It's Working
```bash
# Check if Redis is running
redis-cli ping  # Should return: PONG

# Check Celery worker
celery -A paperweight inspect active

# Check scheduled tasks
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

## 🔧 Configuration Checklist

- [ ] Redis is installed and running on `localhost:6379`
- [ ] Python packages installed: `pip install -r requirements.txt`
- [ ] Database migrated: `python manage.py migrate`
- [ ] `CELERY_BROKER_URL` set in settings.py
- [ ] `CELERY_RESULT_BACKEND` set in settings.py
- [ ] `STRIPE_WEBHOOK_SECRET` configured
- [ ] Celery Beat added to INSTALLED_APPS

## 📅 Scheduled Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| cleanup_expired_orders | Every hour | Mark old pending orders as expired |

## 🎯 Payment Statuses

- `pending` → Payment waiting to be processed
- `completed` → Payment successful, tickets generated
- `failed` → Payment failed, retry triggered
- `incomplete` → Additional verification needed
- `expired` → Order older than 24 hours, no payment

## 🔌 Webhook Endpoint
```
POST /payments/webhook/stripe/
```
Handles: `payment_intent.succeeded`, `payment_intent.payment_failed`

## 📝 Manual Task Triggers
```python
# From Django shell
python manage.py shell

# Manually cleanup expired orders
from notifications.tasks import cleanup_expired_orders
cleanup_expired_orders.delay()

# Manually retry payment
from notifications.tasks import retry_failed_payment
retry_failed_payment.delay(order_id=123)
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "ConnectionRefusedError" | Redis not running. Start: `redis-server` |
| "ModuleNotFoundError: celery" | Install packages: `pip install -r requirements.txt` |
| "No tasks running" | Start Celery: `celery -A paperweight worker -l info` |
| "Beat not scheduling" | Start Beat: `celery -A paperweight beat -l info` |

## 📊 Monitor Orders
```python
from events.models import Order

# View pending orders
Order.objects.filter(payment_status='pending')

# View expired orders
Order.objects.filter(payment_status='expired')

# View failed orders (to retry)
Order.objects.filter(payment_status='failed')

# Orders expiring soon
from django.utils import timezone
from datetime import timedelta
Order.objects.filter(
    expires_at__lt=timezone.now() + timedelta(hours=1),
    payment_status='pending'
)
```

## 🔐 Production Checklist

- [ ] Set `STRIPE_WEBHOOK_SECRET` in environment variables
- [ ] Use RabbitMQ instead of Redis for broker (optional, recommended)
- [ ] Configure Supervisor/systemd for process management
- [ ] Set up log rotation for Celery logs
- [ ] Enable Celery task time limits
- [ ] Test webhook endpoint with Stripe test events
- [ ] Configure email backend for production
- [ ] Set `DEBUG = False` in settings.py
- [ ] Use a process manager like Supervisor or systemd

## 📚 Documentation Files
- `CELERY_SETUP.md` - Complete setup guide
- `IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `start_dev.bat` - Development starter script
- `run_celery.bat` - Celery-only starter script

## 💾 Database Migrations Done
✅ Added `expires_at` field to Order
✅ Added `retry_count` field to Order  
✅ Added `'expired'` to payment_status choices
✅ Applied all django-celery-beat migrations

Run: `python manage.py migrate`

## 🎓 Learn More
- Celery Docs: https://docs.celeryproject.org/
- Django-Celery-Beat: https://github.com/celery/django-celery-beat
- Stripe Webhooks: https://stripe.com/docs/webhooks
