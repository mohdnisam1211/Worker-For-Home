from rest_framework import serializers
from .models import CustomUser, WorkerProfile, CustomerProfile, Booking, Feedback


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone', 'user_type', 'location', 'address']


class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkerProfile
        fields = ['id', 'user', 'service_type', 'experience_years', 'hourly_rate', 'location', 'availability', 'profile_pic']


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'location']


class BookingSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    worker = UserSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'customer', 'worker', 'service', 'date', 'status', 'notes']


class FeedbackSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'booking', 'rating', 'comment']

