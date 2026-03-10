# Paperweight Project - Code Review Report
**Date:** March 10, 2026  
**Reviewer:** Automated Code Analysis  
**Project:** Django Event Ticketing System  
**Status:** Multiple critical issues requiring immediate attention

---

## Executive Summary

The Paperweight application has **25 identified issues** spanning security vulnerabilities, code quality problems, and design flaws. **5 critical issues** require immediate remediation before production deployment. The codebase shows good architectural patterns but lacks proper validation, authentication, and error handling in several key areas.

**Risk Level:** 🔴 **HIGH**  
**Estimated Fix Time:** 2-3 hours for critical issues

---

## 🔴 CRITICAL ISSUES (Must Fix Immediately)

### 1. **Hardcoded API Keys Exposed in Version Control**
- **Location:** `paperweight/settings.py:147-148`
- **Severity:** CRITICAL
- **Issue:** Stripe public and secret keys hardcoded
  ```python
  STRIPE_PUBLIC_KEY = 'pk_test_51R5S6vG6zMRuLBLH...'
  STRIPE_SECRET_KEY = 'sk_test_51R5S6vG6zMRuLBLH...'
  ```
- **Risk:** Anyone with repository access can access Stripe account, make charges, refund payments
- **Fix:**
  1. Revoke current keys in Stripe dashboard immediately
  2. Create new keys
  3. Move to `.env` file:
     ```python
     STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
     STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
     ```
  4. Add `.env` to `.gitignore`
  5. Use `python-dotenv` to load environment variables

---

### 2. **Database Password Empty/Missing**
- **Location:** `paperweight/settings.py:84`
- **Severity:** CRITICAL
- **Issue:** 
  ```python
  'PASSWORD': '',  # No password set
  ```
- **Risk:** Anyone on network can connect to MySQL database without authentication
- **Fix:**
  1. Set strong MySQL password
  2. Move to environment variable:
     ```python
     'PASSWORD': os.environ.get('DB_PASSWORD'),
     ```

---

### 3. **Migration Code in models.py**
- **Location:** `events/models.py:9-45`
- **Severity:** CRITICAL
- **Issue:** Django Migration class defined in models.py instead of migrations folder
  ```python
  class Migration(migrations.Migration):
      dependencies = [('events', '0001_initial')]
      operations = [...]  # 40+ lines of migration code
  ```
- **Risk:** 
  - Causes migration conflicts
  - Can lead to data corruption on `makemigrations`
  - Breaks team collaboration
- **Fix:** 
  1. Delete entire `Migration` class from models.py
  2. Run `python manage.py makemigrations` to regenerate properly
  3. Run `python manage.py migrate` to apply

---

### 4. **Webhook Endpoint Not Protected**
- **Location:** `payments/views.py:stripe_webhook()` 
- **Severity:** CRITICAL
- **Issue:** Payment webhook lacks authentication
  ```python
  def stripe_webhook(request):  # No @csrf_exempt or signature verification
      # Directly processes payment updates
  ```
- **Risk:** 
  - Attackers can forge webhook events
  - Create fake "payment.succeeded" events
  - Grant tickets without payment
- **Fix:**
  ```python
  from django.views.decorators.csrf import csrf_exempt
  from django.views.decorators.http import require_http_methods
  import stripe
  
  @csrf_exempt
  @require_http_methods(["POST"])
  def stripe_webhook(request):
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
      
      # Process verified event only
  ```

---

### 5. **Duplicate Settings Configuration**
- **Location:** `paperweight/settings.py`
- **Severity:** CRITICAL
- **Issue:** Settings defined multiple times with conflicting values
  ```python
  # Lines 100-105
  MEDIA_URL = '/media/'
  MEDIA_ROOT = BASE_DIR / 'media'
  
  # Lines 122-124 (repeated)
  MEDIA_URL = '/media/'
  MEDIA_ROOT = BASE_DIR / 'media'
  
  # Lines 135-142 vs 148-154 (Celery config - DIFFERENT VALUES!)
  CELERY_BROKER_URL = 'redis://localhost:6379/0'      # Line 135
  CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Line 136
  CELERY_ACCEPT_CONTENT = ['json']                     # Line 137
  
  # Lines 148-154 (conflicting)
  CELERY_RESULT_BACKEND = 'django-db'  # Line 151 - conflicts with line 136!
  CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Line 154
  ```
- **Risk:** 
  - Celery results routing to Django DB instead of Redis (one copy, then Redis)
  - Undefined behavior on which config is used
- **Fix:** Remove all duplicates, keep only one copy of each setting

---

## 🟠 HIGH-PRIORITY SECURITY ISSUES

### 6. **Missing Permission Checks on Event Edit**
- **Location:** `events/views.py:edit_event()`
- **Severity:** HIGH
- **Issue:** No verification that user owns the event
  ```python
  def edit_event(request, event_id):
      event = get_object_or_404(Event, id=event_id)
      # Any user can edit ANY event!
  ```
- **Risk:** Users can modify other users' events, change prices, details
- **Fix:**
  ```python
  def edit_event(request, event_id):
      event = get_object_or_404(Event, id=event_id)
      if event.created_by != request.user:
          return redirect('index')  # or raise PermissionDenied
  ```

---

### 7. **Missing Permission Checks on Event Delete**
- **Location:** `events/views.py:delete_event()`
- **Severity:** HIGH
- **Issue:** No ownership verification before deletion
- **Fix:** Add same check as edit_event

---

### 8. **No Authentication on Sensitive Endpoints**
- **Location:** `payments/views.py:pay_event_fee()` and `users/views.py:approve_payout()`
- **Severity:** HIGH
- **Issue:** Admin functions missing superuser check
  ```python
  def reject_payout(request, request_id):  # No @login_required check if admin
      commission_request = CommissionRequest.objects.get(id=request_id)
  ```
- **Fix:** Add `if not request.user.is_superuser: return redirect('index')`

---

### 9. **SQL Injection-like Risk in Search**
- **Location:** `events/views.py:search():23`
- **Severity:** HIGH
- **Issue:** 
  ```python
  created_by = request.GET.get('created_by', '')  # Direct GET parameter
  if created_by:
      events = events.filter(created_by__username=created_by)
  ```
- **Risk:** Potential for abuse, though Django ORM provides some protection
- **Fix:** Validate input is alphanumeric or use dropdown list:
  ```python
  if created_by and len(created_by) < 50:
      events = events.filter(created_by__username=created_by)
  ```

---

### 10. **File Upload Vulnerability**
- **Location:** `events/forms.py` EventForm and `events/views.py:create_event()`
- **Severity:** HIGH
- **Issue:** No validation on uploaded images
  ```python
  image = models.ImageField(upload_to='event_images/', null=True, blank=True)
  # No file type, size, or content validation
  ```
- **Risk:** Users can upload malicious files, oversized files
- **Fix:**
  ```python
  from django.core.exceptions import ValidationError
  
  def validate_image_file(file):
      if file.size > 5 * 1024 * 1024:  # 5MB limit
          raise ValidationError("Image too large (max 5MB)")
      if file.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
          raise ValidationError("Only JPEG, PNG, GIF allowed")
  
  image = models.ImageField(upload_to='event_images/', 
                           validators=[validate_image_file],
                           null=True, blank=True)
  ```

---

### 11. **No CSRF Protection on Payment Forms**
- **Location:** `payments/templates/checkout.html`
- **Severity:** HIGH
- **Issue:** Stripe form submission may lack CSRF token
- **Fix:** Ensure form includes `{% csrf_token %}`

---

## 🟡 MEDIUM-PRIORITY CODE ISSUES

### 12. **Missing Decimal Import**
- **Location:** `users/views.py:70`
- **Severity:** MEDIUM
- **Issue:**
  ```python
  from decimal import Decimal  # Missing!
  
  commission = Decimal(event.price) * Decimal(0.60)  # NameError
  ```
- **Fix:** Add `from decimal import Decimal` at top of file

---

### 13. **Variable Scope Bug in checkout()**
- **Location:** `payments/views.py:48-50`
- **Severity:** MEDIUM
- **Issue:**
  ```python
  for event_id, quantity in cart.items():
      event = Event.objects.get(id=int(event_id))
      # ... loop ends
  
  if event.available_tickets < quantity:  # ❌ event undefined if cart empty!
      messages.error(request, ...)
  ```
- **Risk:** NameError if cart is empty
- **Fix:** Move check inside loop or validate non-empty first:
  ```python
  for event_id, quantity in cart.items():
      event = Event.objects.get(id=int(event_id))
      if event.available_tickets < quantity:
          messages.error(...)
          return redirect('view_cart')
  ```

---

### 14. **Duplicate Imports in models.py**
- **Location:** `events/models.py:1-8`
- **Severity:** MEDIUM
- **Issue:**
  ```python
  from django.db import models  # Line 1
  from django.db import migrations  # Line 5
  from django.db import migrations  # Line 7 (duplicate!)
  from django.db import models  # Line 8 (duplicate!)
  ```
- **Fix:** Remove duplicates, keep single import per line

---

### 15. **Unused Imports**
- **Location:** Multiple files
- **Severity:** MEDIUM
- **Issue:**
  ```python
  # events/views.py
  from .utils import process_order  # Imported but never called
  
  # events/models.py
  from django.shortcuts import render  # Models don't render
  
  # payments/views.py
  logger = logging.getLogger(__name__)  # Created but rarely used
  ```
- **Fix:** Remove unused imports to improve readability

---

### 16. **Inconsistent Error Handling**
- **Location:** Throughout views
- **Severity:** MEDIUM
- **Issue:** Some functions use try/except, others don't handle exceptions
  ```python
  # Has error handling:
  try:
      payment_intent = stripe.PaymentIntent.create(...)
  except stripe.error.StripeError as e:
      messages.error(request, f"Payment setup failed: {str(e)}")
  
  # Missing error handling:
  event = Event.objects.get(id=event_id)  # Can raise DoesNotExist
  commission_request = CommissionRequest.objects.get(id=request_id)  # No try/except
  ```
- **Fix:** Add consistent try/except pattern to all queries

---

### 17. **Race Condition in Order Creation**
- **Location:** `payments/views.py:checkout()`
- **Severity:** MEDIUM
- **Issue:** Two simultaneous requests can both create orders
  ```python
  if request.method == 'POST':
      order = Order.objects.create(...)  # No uniqueness constraint or lock
  ```
- **Risk:** Double orders possible
- **Fix:** Use transaction atomicity:
  ```python
  from django.db import transaction
  
  with transaction.atomic():
      order = Order.objects.create(...)
  ```

---

### 18. **Expired Orders Not Checked**
- **Location:** `payments/views.py:payment_success()`
- **Severity:** MEDIUM
- **Issue:** Order expires_at set but never verified on success
  ```python
  def payment_success(request, order_id):
      order = get_object_or_404(Order, id=order_id)
      # No check: if order.expires_at < now() -> reject
  ```
- **Fix:**
  ```python
  if timezone.now() > order.expires_at:
      messages.error(request, 'Order has expired')
      return redirect('checkout')
  ```

---

### 19. **No Inventory Lock During Checkout**
- **Location:** `events/views.py:add_to_cart()` and `payments/views.py:checkout()`
- **Severity:** MEDIUM
- **Issue:** Tickets added to cart but never reserved
  ```python
  # Cart has tickets, but event.available_tickets could be reduced before payment
  ```
- **Risk:** Overbooking if multiple users buy same tickets
- **Fix:** Atomically update inventory on order creation:
  ```python
  from django.db.models import F
  
  event.available_tickets = F('available_tickets') - quantity
  event.save()
  ```

---

## 🟡 DESIGN & LOGIC ISSUES

### 20. **Pagination Missing on Admin Dashboard**
- **Location:** `users/views.py:admin_dashboard():50`
- **Severity:** MEDIUM
- **Issue:**
  ```python
  reports = Report.objects.all()  # No pagination
  commission_requests = CommissionRequest.objects.all()  # Could be 10K+ rows
  ```
- **Risk:** Page loads slowly with thousands of records
- **Fix:** Add pagination:
  ```python
  from django.core.paginator import Paginator
  
  paginator = Paginator(Report.objects.all(), 50)
  page_number = request.GET.get('page', 1)
  reports = paginator.get_page(page_number)
  ```

---

### 21. **Ticket Status Never Updated**
- **Location:** `events/models.py:168`
- **Severity:** MEDIUM
- **Issue:** 
  ```python
  status = models.CharField(max_length=10, 
                           choices=[('valid', 'Valid'), ('used', 'Used'), ('expired', 'Expired')],
                           default='valid')
  # Set to 'valid' but verify_ticket() never updates to 'used'
  ```
- **Risk:** Can scan same ticket multiple times
- **Fix:** Update status in verify_ticket:
  ```python
  def verify_ticket(request, ticket_id):
      ticket = get_object_or_404(Ticket, id=ticket_id)
      if ticket.status == 'used':
          return error("Ticket already scanned")
      ticket.status = 'used'
      ticket.used_at = timezone.now()
      ticket.save()
  ```

---

### 22. **No Email Verification on Newsletter**
- **Location:** `events/models.py:171-176`
- **Severity:** MEDIUM
- **Issue:**
  ```python
  class NewsletterSubscriber(models.Model):
      email = models.EmailField(unique=True)
      # Direct subscribe without verification
  ```
- **Risk:** Spam, invalid emails, email enumeration attacks
- **Fix:** Add token-based double opt-in:
  ```python
  token = models.CharField(max_length=100)
  verified = models.BooleanField(default=False)
  ```

---

### 23. **No Soft Deletes**
- **Location:** All models
- **Severity:** MEDIUM
- **Issue:** Deleting events/orders cascades permanently
  ```python
  event = models.ForeignKey(Event, on_delete=models.CASCADE)  # Deletes all related orders
  ```
- **Risk:** Data loss, cannot audit deleted records
- **Fix:** Implement soft deletes:
  ```python
  class Event(models.Model):
      deleted_at = models.DateTimeField(null=True, blank=True)
      
      class Manager(models.Manager):
          def get_queryset(self):
              return super().get_queryset().filter(deleted_at__isnull=True)
  ```

---

### 24. **Event Date Validation Missing**
- **Location:** `events/forms.py` and `events/models.py`
- **Severity:** MEDIUM
- **Issue:** Can create events in the past
  ```python
  start_datetime = models.DateTimeField()  # No validation
  ```
- **Fix:**
  ```python
  def clean(self):
      if self.start_datetime < timezone.now():
          raise ValidationError("Event cannot be in the past")
  ```

---

### 25. **Minimal Logging of Critical Operations**
- **Location:** `payments/views.py`, `events/views.py`
- **Severity:** LOW-MEDIUM
- **Issue:** No audit trail for payments, order changes
  ```python
  def payment_success(...):
      # No logging of successful payment
  ```
- **Fix:** Add logging:
  ```python
  logger.info(f"Payment completed for order {order.id} by {order.email} - Amount: {order.total_amount}")
  logger.info(f"Event {event.id} approved by {request.user.username}")
  ```

---

## 📊 Issue Summary Table

| Priority | Category | Count | Examples |
|----------|----------|-------|----------|
| 🔴 CRITICAL | Security | 5 | API keys, DB password, webhook auth, duplicates, migrations |
| 🟠 HIGH | Security | 7 | Permissions, file upload, CSRF, injection risk |
| 🟡 MEDIUM | Code Quality | 13 | Imports, scope, error handling, logic, audit |
| **Total** | | **25** | |

---

## 🛠️ Remediation Plan

### Phase 1: Immediate (DO TODAY)
- [ ] Remove Migration class from events/models.py
- [ ] Move API keys to .env file
- [ ] Set database password
- [ ] Remove duplicate settings
- [ ] Add Stripe webhook signature verification
- [ ] Add permission checks to edit_event and delete_event

**Time:** ~30 minutes

### Phase 2: High Priority (DO THIS WEEK)
- [ ] Add Decimal import to users/views.py
- [ ] Fix variable scope in checkout()
- [ ] Add error handling to database queries
- [ ] Add transactional locks to order creation
- [ ] Implement file upload validation
- [ ] Check order expiration in payment_success

**Time:** ~60 minutes

### Phase 3: Medium Priority (DO BEFORE LAUNCH)
- [ ] Add pagination to admin dashboard
- [ ] Update ticket status on verification
- [ ] Add event date validation
- [ ] Remove unused imports
- [ ] Standardize error handling across all views
- [ ] Implement soft deletes (optional but recommended)

**Time:** ~90 minutes

### Phase 4: Polish (NICE-TO-HAVE)
- [ ] Add comprehensive logging
- [ ] Email verification for newsletter
- [ ] Rate limiting on payment endpoints
- [ ] API documentation
- [ ] Unit tests for payment flow

**Time:** ~120 minutes

---

## 🚀 Deployment Checklist

Before moving to production, verify:
- [ ] All CRITICAL issues resolved
- [ ] All HIGH issues resolved  
- [ ] SECRET_KEY changed from default
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS properly configured
- [ ] CSRF_TRUSTED_ORIGINS updated for production domain
- [ ] Email configuration working (test send)
- [ ] Redis/Celery running and functional
- [ ] Database backups automated
- [ ] Error monitoring enabled (e.g., Sentry)
- [ ] Rate limiting implemented
- [ ] SSL certificate installed
- [ ] Static files collected (`python manage.py collectstatic`)

---

## References & Best Practices

1. **Django Security:** https://docs.djangoproject.com/en/4.2/topics/security/
2. **Stripe Webhook Security:** https://stripe.com/docs/webhooks
3. **OWASP Top 10:** https://owasp.org/www-project-top-ten/
4. **Python-Dotenv:** https://python-dotenv.readthedocs.io/
5. **Django Transaction Management:** https://docs.djangoproject.com/en/4.2/topics/db/transactions/

---

**Report Generated:** March 10, 2026  
**Next Review Date:** After remediation completion  
**Reviewer:** Automated Code Analysis System
