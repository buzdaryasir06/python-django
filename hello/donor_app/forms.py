from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import User
from django.core.validators import validate_email
#from django.contrib.gis.geos import Point

class BloodDonorRegistrationForm(UserCreationForm):
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    latitude = forms.FloatField()
    longitude = forms.FloatField()
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect
    )
    province = forms.CharField(max_length=50, required=True)
    city = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'phone', 'blood_type',
            'user_type', 'latitude', 'longitude', 'province', 'city'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Store as "lat,lon" string
        user.location = f"{self.cleaned_data['latitude']},{self.cleaned_data['longitude']}"
        if commit:
            user.save()
            return user
    
class BloodDonorLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    
    error_messages = {
        'invalid_login': "Invalid email or password.",
        'inactive': "This account is inactive.",
        'unverified': "Please verify your email first."
    }

class UserProfileForm(UserChangeForm):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    password = None  # Remove password field
    
    class Meta:
        model = User
        fields = [
            'profile_picture', 'first_name', 'last_name', 'email', 
            'phone', 'blood_type', 'bio', 'address', 'city', 'country',
            'latitude', 'longitude'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.location:
            self.fields['latitude'].initial = self.instance.location.y
            self.fields['longitude'].initial = self.instance.location.x
    
    def save(self, commit=True):
        user = super().save(commit=False)
        latitude = self.cleaned_data.get('latitude')
        longitude = self.cleaned_data.get('longitude')
        
        if latitude is not None:
            user.latitude = float(latitude)
        if longitude is not None:
            user.longitude = float(longitude)
        
        if commit:
            user.save()
        return user

class DonorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_available']
        widgets = {
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }