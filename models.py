from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Custom User
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# Worker Profile 
class WorkerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=100, blank=True, null=True)
    experience_years = models.IntegerField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("available", "Available"), ("busy", "Busy"), ("on_leave", "On Leave")],
        default="available"
    )
    profile_pic = models.ImageField(upload_to="worker_profiles/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_type or 'No Service'}"

# Customer Profile
class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)  

    def __str__(self):
        return self.user.username



# Booking 
class Booking(models.Model):
    worker = models.ForeignKey(CustomUser, related_name="bookings", on_delete=models.CASCADE)
    customer = models.ForeignKey(CustomUser, related_name="customer_bookings", on_delete=models.CASCADE)
    service = models.CharField(max_length=100)
    date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer.username} → {self.worker.username} ({self.service})"


# Feedback
class Feedback(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="feedback")
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Feedback for {self.booking}"

