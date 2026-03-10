from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render
from django.db import migrations
from django.core.exceptions import ValidationError
from django.db import migrations
from django.db import models

def set_default_datetimes(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    for event in Event.objects.all():
        if event.date:
            start_time = timezone.datetime.combine(event.date, timezone.datetime.min.time())
            end_time = timezone.datetime.combine(event.date, timezone.datetime.max.time())
            event.start_datetime = timezone.make_aware(start_time, timezone.get_default_timezone())
            event.end_datetime = timezone.make_aware(end_time, timezone.get_default_timezone())
            event.save()

class Migration(migrations.Migration):
    dependencies = [
        ('events', '0001_initial'),  # Adjust based on your previous migration
    ]
    operations = [
        migrations.AddField(
            model_name='event',
            name='start_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='end_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(set_default_datetimes),
        migrations.AlterField(
            model_name='event',
            name='start_datetime',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_datetime',
            field=models.DateTimeField(),
        ),
    ]


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
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

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start datetime must be before end datetime.")

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

    def __str__(self):
        return self.email
