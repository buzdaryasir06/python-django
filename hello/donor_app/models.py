from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('donor', 'Blood Donor'),
        ('seeker', 'Blood Seeker'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'"
    )
    phone = models.CharField(validators=[phone_regex], max_length=17)
    blood_type = models.CharField(max_length=3)
    is_available = models.BooleanField(default=True)
    last_donation = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        default='profile_pics/default.png',
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class LoginActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    success = models.BooleanField(default=False)

# blood request model
class BloodRequest(models.Model):
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blood_type = models.CharField(max_length=3)
    units_required = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Request for {self.blood_type} by {self.user.username}"

# notification model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('request', 'New Blood Request'),
        ('match', 'Donor Match'),
        ('message', 'New Message'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    related_url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"