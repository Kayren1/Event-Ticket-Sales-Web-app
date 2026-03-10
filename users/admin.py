from django.contrib import admin
from django.contrib.auth.models import User  # Import the User model
from events.models import Event

# Remove this line if User is already registered elsewhere
# admin.site.register(User)
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_datetime', 'end_datetime']
    list_filter = ['start_datetime']
    search_fields = ['title']
