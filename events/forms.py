from django import forms
from django.core.exceptions import ValidationError
from .models import Event, Report

def validate_image_file(file):
    """Validate uploaded image file - check size and content type."""
    if file.size > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("Image file is too large. Maximum size is 5MB.")
    
    # Check file extension
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    file_ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
    if file_ext not in valid_extensions:
        raise ValidationError(f"Invalid image format. Allowed formats: {', '.join(valid_extensions)}")

class EventForm(forms.ModelForm):
    image = forms.ImageField(required=False, validators=[validate_image_file])
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'start_datetime', 'end_datetime', 'location', 'price', 'available_tickets', 'image']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'category': forms.Select(),
        }
    
    def clean(self):
        """Additional validation for form fields."""
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        # Validate event date is not in the past
        if start_datetime and start_datetime < forms.DateTimeField().to_python(forms.widgets.DateTimeInput().value_from_datadict(
            {'datetime': 'now'}, {}, 'datetime')):
            from django.utils import timezone
            if start_datetime < timezone.now():
                raise ValidationError("Event start date cannot be in the past.")
        
        # Validate end date is after start date
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise ValidationError("Event end date must be after start date.")
        
        return cleaned_data

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['message']