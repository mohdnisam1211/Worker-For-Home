from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.db.models import Avg
import logging
from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException
from .forms import *  
from .models import *
User = get_user_model()

# Home + Search
def home(request):
    query = request.GET.get("q", "")
    workers = WorkerProfile.objects.all().annotate(
        avg_rating=Avg("user__bookings__feedback__rating")
    )
    if query:
        workers = workers.filter(
            Q(user__username__icontains=query) |
            Q(service_type__icontains=query) |
            Q(location__icontains=query)
        )
    return render(request, 'home.html', {'workers': workers, 'query': query})


def search_workers(request):
    query = request.GET.get("q", "")
    workers = WorkerProfile.objects.all()
    if query:
        workers = workers.filter(
            Q(user__username__icontains=query)
            | Q(service_type__icontains=query)
            | Q(location__icontains=query)
        )
    return render(request, "searchresults.html", {"workers": workers, "query": query})

# Register
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            messages.success(request, f"Account created for {user.username}")
            login(request, user)
            if user.role == "worker":
                return redirect("worker_dashboard")
            elif user.role == "customer":
                return redirect("customer_dashboard")
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

# Login / Logout
def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome {user.username}")
            if user.role == "worker":
                return redirect("worker_dashboard")
            elif user.role == "customer":
                return redirect("customer_dashboard")
            elif user.role == "admin":
                return redirect("/admin/")
            return redirect("home")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")

# Worker: Profile + Dashboard
@login_required
def worker_profile(request):
    profile, created = WorkerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "service_type": "General",
            "experience_years": 0,
            "hourly_rate": 0.0,
            "location": request.user.location or "",
            "status": "available",
        }
    )
    avg_rating = Feedback.objects.filter(booking__worker=profile.user).aggregate(
        Avg("rating")
    )["rating__avg"]
    if request.method == "POST":
        form = WorkerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("worker_profile")
    else:
        form = WorkerProfileForm(instance=profile)
    return render(
        request,
        "workerprofile.html",
        {"form": form, "profile": profile, "avg_rating": avg_rating},
    )



@login_required
def edit_worker_profile(request):
    profile, created = WorkerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "service_type": "General",
            "experience_years": 0,
            "hourly_rate": 0.0,
            "location": request.user.location or "",
            "status": "available",
        }
    )
    if request.method == "POST":
        form = WorkerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("worker_dashboard")
    else:
        form = WorkerProfileForm(instance=profile)
    return render(request, "editworkerprofile.html", {"form": form})

@login_required
def worker_dashboard(request):
    if request.user.role != "worker":
        messages.error(request, "Only workers can access the dashboard.")
        return redirect("home")
    profile = WorkerProfile.objects.filter(user=request.user).first()
    jobs = Booking.objects.filter(worker=request.user).order_by("-date")
    return render(request, "workerdashboard.html", {"profile": profile, "jobs": jobs})

@login_required
def update_worker_status(request):
    if request.method == "POST":
        profile = request.user.workerprofile
        new_status = request.POST.get("status")
        if new_status:
            profile.status = new_status
            profile.save()
            messages.success(request, f"Status updated to {profile.status}")
    return redirect("worker_dashboard")

@login_required
def delete_worker_profile(request):
    if request.user.role != "worker":
        messages.error(request, "Only workers can delete their profile.")
        return redirect("home")
    try:
        profile = request.user.workerprofile
    except WorkerProfile.DoesNotExist:
        messages.error(request, "You don’t have a profile to delete.")
        return redirect("worker_dashboard")
    if request.method == "POST":
        profile.delete()
        messages.success(request, "Your profile has been deleted.")
        return redirect("home")
    return render(request, "deleteworkerprofile.html", {"profile": profile})

# Worker: Booking Actions
@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, worker=request.user)
    booking.status = "confirmed"
    booking.save()
    messages.success(request, "Booking accepted successfully.")
    return redirect("worker_dashboard")

@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, worker=request.user)
    booking.status = "cancelled"
    booking.save()
    messages.success(request, "Booking rejected.")
    return redirect("worker_dashboard")

@login_required
def complete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, worker=request.user)
    if booking.status == "confirmed":
        booking.status = "completed"
        booking.save()
        messages.success(request, "Booking marked as completed.")
    else:
        messages.error(request, "Only confirmed bookings can be completed.")
    return redirect("worker_dashboard")

# Customer: Profile + Dashboard
@login_required
def customer_dashboard(request):
    if request.user.role != "customer":
        messages.error(request, "Only customers can access this page.")
        return redirect("home")
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    bookings = Booking.objects.filter(customer=request.user).select_related("worker")
    return render(request, "customerdashboard.html", {"profile": profile, "bookings": bookings})

@login_required
def customer_profile(request):
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        location = request.POST.get("location")
        phone = request.POST.get("phone")
        request.user.phone = phone
        request.user.save()
        profile.location = location
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("customer_dashboard")
    return render(request, "customerprofile.html", {"profile": profile})

@login_required
def edit_customer_profile(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    if request.method == "POST":
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("customer_profile")
    else:
        form = CustomerProfileForm(instance=profile)
    return render(request, "editcustomerprofile.html", {"form": form})

@login_required
def worker_view_customer_profile(request, customer_id):
    if request.user.role != "worker":
        messages.error(request, "Only workers can view customer profiles.")
        return redirect("home")
    customer = get_object_or_404(User, id=customer_id, role="customer")
    profile = getattr(customer, "customerprofile", None)
    return render(request, "workertocustomer.html", {"customer": customer, "profile": profile})

# Booking: Create + Cancel + Feedback
logger = logging.getLogger(__name__)  
@login_required
def create_booking(request, worker_id):
    worker = get_object_or_404(WorkerProfile, id=worker_id)
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.worker = worker.user
            booking.save()
            try:
                subject = "New Booking Confirmation"
                message = f"""
                Hello {worker.user.username},
                You have a new booking request!
                Service: {booking.service}
                Date: {booking.date}
                Customer: {request.user.username}
                Location: {request.user.location}
                Please log in to your dashboard to accept/reject.
                """
                send_mail(
                    subject,
                    message,
                    "yourgmail@gmail.com", 
                    [worker.user.email],
                    fail_silently=False, 
                )
                messages.success(request, "Booking created and email notification sent.")
            except (BadHeaderError, SMTPException, Exception) as e:
                logger.error(f"Email sending failed: {e}") 
                messages.warning(request, "Booking created, but email could not be sent.")
            return redirect("customer_dashboard")
    else:
        form = BookingForm()
    return render(request, "createbooking.html", {"form": form, "worker": worker})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    if booking.status == "cancelled":
        messages.info(request, "This booking is already cancelled.")
    else:
        booking.status = "cancelled"
        booking.save()
        messages.success(request, "Your booking has been cancelled.")
    return redirect("customer_dashboard")

@login_required
def leave_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    feedback = Feedback.objects.filter(booking=booking).first()
    if request.method == "POST":
        form = FeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.booking = booking
            feedback.save()
            messages.success(request, "Feedback submitted successfully.")
            return redirect("customer_dashboard")
    else:
        form = FeedbackForm(instance=feedback)
    return render(request, "leavefeedback.html", {"form": form, "booking": booking})


# Admin: Delete Users / Workers
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "You cannot delete a superuser.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect("home")

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == "admin")
def delete_worker(request, worker_id):
    worker = get_object_or_404(WorkerProfile, id=worker_id)
    user = worker.user
    worker.delete()
    user.delete()
    messages.success(request, "Worker deleted successfully.")
    return redirect("home")

