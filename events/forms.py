from django import forms
from .models import Event, Report

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'start_datetime', 'end_datetime', 'location', 'price', 'available_tickets', 'image']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'category': forms.Select(),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['message']