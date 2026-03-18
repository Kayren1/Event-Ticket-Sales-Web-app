from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    CATEGORIES = [
        ('concert', 'Concert'),
        ('conference', 'Conference'),
        ('festival', 'Festival'),
        ('sports', 'Sports'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('party', 'Party'),
        ('theatre', 'Theatre'),
        ('exhibition', 'Exhibition'),
        ('comedy', 'Comedy'),
        ('religious', 'Religious'),
        ('fundraiser', 'Fundraiser'),
        ('networking', 'Networking'),
        ('other', 'Other'),
    ]
    CATEGORY_CHOICES = CATEGORIES
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_tickets = models.PositiveIntegerField()
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete field

    class Manager(models.Manager):
        """Custom manager to exclude soft-deleted events."""
        def get_queryset(self):
            return super().get_queryset().filter(deleted_at__isnull=True)
    
    objects = Manager()
    all_objects = models.Manager()  # Access all events including deleted

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start datetime must be before end datetime.")
        if self.start_datetime < timezone.now():
            raise ValidationError("Event start date cannot be in the past.")

    def soft_delete(self):
        """Soft delete the event."""
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class CommissionRequest(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    planner = models.ForeignKey(User, on_delete=models.CASCADE)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission Request for {self.event.title} by {self.planner.username}"

class CreationFeePayment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_intent_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.event.title} - {self.status}"

class Order(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Order expires after 24 hours
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('incomplete', 'Incomplete'),
            ('expired', 'Expired'),
        ],
        default='pending'
    )
    payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    retry_count = models.IntegerField(default=0)  # Track payment retry attempts
    
    def __str__(self):
        return f"Order {self.id} by {self.email}"

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=[('valid', 'Valid'), ('used', 'Used'), ('expired', 'Expired')], default='valid')
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket {self.code} for {self.event.title}"

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.username}"
    
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=100, blank=True, null=True)  # Email verification token
    verified = models.BooleanField(default=False)  # Email verification status
    unsubscribed_at = models.DateTimeField(null=True, blank=True)  # Unsubscribe timestamp

    def __str__(self):
        return self.email
