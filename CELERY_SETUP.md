# Celery & Celery Beat Setup Guide

## Overview
This application uses Celery for asynchronous task processing and Celery Beat for scheduling periodic tasks like cleaning up expired orders.

## Prerequisites
- Redis server running on localhost:6379
- All packages installed from requirements.txt

## Setup Steps

### 1. Start Redis Server
Before running Celery, you need Redis running. On Windows:

```bash
# Option 1: If you have Redis installed locally
redis-server

# Option 2: Or use Windows Subsystem for Linux (WSL)
wsl redis-server
```

### 2. Run Celery Worker and Beat

#### Option A: Using the Batch Script (Windows)
Double-click `run_celery.bat` - this will start both the worker and beat scheduler in separate windows.

#### Option B: Manual Commands (Any OS)

**Terminal 1 - Start Celery Worker:**
```bash
celery -A paperweight worker -l info
```

**Terminal 2 - Start Celery Beat:**
```bash
celery -A paperweight beat -l info
```

### 3. Verify it's Working

#### Check Worker Status:
```bash
celery -A paperweight inspect active
```

#### Check Scheduled Tasks:
In Django admin, go to:
- Admin Dashboard → Periodic Tasks
- You should see "cleanup-expired-orders" scheduled to run hourly

## How It Works

### Scheduled Tasks
1. **Cleanup Expired Orders** (Runs every hour)
   - Marks pending orders as "expired" if they're over 24 hours old
   - Frees up cart slots for abandoned checkouts
   - Task: `notifications.tasks.cleanup_expired_orders`

### Payment Failure Handling
1. **Payment Intent Failed** (Triggered by Stripe webhook)
   - When Stripe detects a payment failure
   - Automatically triggers retry task
   - Max 3 retry attempts per order

### Manual Task Triggering
You can manually trigger tasks from Django shell:

```bash
python manage.py shell
```

```python
from notifications.tasks import cleanup_expired_orders
cleanup_expired_orders.delay()
```

## Configuration

### Redis Connection
In `settings.py`:
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### Celery Beat Schedule
In `settings.py`:
```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-orders': {
        'task': 'notifications.tasks.cleanup_expired_orders',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### Stripe Webhook Secret
Set in environment or `settings.py`:
```python
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_test_secret')
```

## Troubleshooting

### Tasks not running?
1. Check Redis is running: `redis-cli ping` (should return "PONG")
2. Check worker is running: `celery -A paperweight inspect active`
3. Check beat is running: Look for "Beat" window/terminal
4. Check logs for errors in worker terminal

### Worker crashes?
```bash
# Restart worker
celery -A paperweight worker -l info --concurrency=4
```

### Memory issues?
```bash
# Limit worker pool size
celery -A paperweight worker -l info --concurrency=2
```

## Production Deployment

For production, use a process manager:

### Using Supervisor (Linux/Mac)
Create `/etc/supervisor/conf.d/paperweight-celery.conf`:
```ini
[program:paperweight-celery-worker]
command=/path/to/venv/bin/celery -A paperweight worker -l info
directory=/path/to/paperweight
user=www-data
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600

[program:paperweight-celery-beat]
command=/path/to/venv/bin/celery -A paperweight beat -l info
directory=/path/to/paperweight
user=www-data
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
```

### Using Docker
Include Celery services in docker-compose.yml.

## Available Tasks

### cleanup_expired_orders
- Cleans up pending/failed orders older than 24 hours
- Marks them as "expired"
- Runs: Every hour

### retry_failed_payment
- Retries failed payment for an order
- Max 3 attempts
- Triggered: Automatically on payment failure via webhook

### send_payment_confirmation
- Sends email confirmation with ticket details
- Triggered: After successful payment
- Task ID: Stored in payment confirmation

## Monitoring

### View Active Tasks
```bash
celery -A paperweight inspect active
```

### View Task Statistics
```bash
celery -A paperweight inspect stats
```

### View Registered Tasks
```bash
celery -A paperweight inspect registered
```

## Notes
- All times are in UTC (configurable in settings.py)
- Tasks are stored in Redis by default
- Results are also stored in Redis
- For persistence, use RabbitMQ as broker in production
