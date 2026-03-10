from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class EventPlannerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Add the user to the 'EventPlanners' group
            group, created = Group.objects.get_or_create(name='EventPlanners')
            group.user_set.add(user)
        return user