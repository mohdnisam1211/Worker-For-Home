from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, WorkerProfile, Booking, Feedback, CustomerProfile


# User Registration
class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'spellcheck': 'false'})
    )

    role = forms.ChoiceField(
        choices=[('customer', 'Customer'), ('worker', 'Worker')],
        required=True,
        label="Account Type"
    )

    service_type = forms.CharField(
        max_length=100,
        required=False,
        label="Service Type (only for workers)",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Plumber, Electrician, Cleaner"})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username", "email", "phone", "location", "role",
            "password1", "password2", "service_type"
        )
def save(self, commit=True):
    user = super().save(commit=False)
    user.role = self.cleaned_data["role"]
    if commit:
        user.save()
        if user.role == "worker":
            WorkerProfile.objects.create(
                user=user,
                service_type=self.cleaned_data.get("service_type", "General"),
                experience_years=0,
                hourly_rate=0,
                location=user.location,
                status="available"
            )
        elif user.role == "customer":
            CustomerProfile.objects.create(user=user, location="")
    return user

# Login
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'spellcheck': 'false'})
    )
    password = forms.CharField(widget=forms.PasswordInput)


# Worker Profile
class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerProfile
        fields = ['service_type', 'experience_years', 'hourly_rate', 'location', 'status', 'profile_pic']

        widgets = {
            "service_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter service type"}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "hourly_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter location"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


# Booking
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'date', 'notes']

        widgets = {
            'service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service required'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Additional notes'}),
        }


# Feedback
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']

        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i} Stars") for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write your feedback here...'}),
        }


# Customer Profile
class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ["location", "phone"]

        widgets = {
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your location"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your phone number"}),
        }
