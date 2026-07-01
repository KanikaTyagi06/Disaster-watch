"""
earthquake_app/forms.py
Form definitions for login, registration, and data fetch.
"""
from django import forms
from django.core.exceptions import ValidationError
from datetime import date


class LoginForm(forms.Form):
    """User login form."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter username",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password",
        }),
    )


class RegisterForm(forms.Form):
    """New user registration form."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Choose a username"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}),
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password (min 6 chars)"}),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}),
    )

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get("password")
        pw2 = cleaned.get("confirm_password")
        if pw1 and pw2 and pw1 != pw2:
            raise ValidationError("Passwords do not match.")
        return cleaned


class FetchDataForm(forms.Form):
    """Form to trigger a USGS earthquake data fetch."""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "max": str(date.today()),
        }),
        label="Start Date",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "max": str(date.today()),
        }),
        label="End Date",
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end   = cleaned.get("end_date")
        if start and end:
            if end < start:
                raise ValidationError("End date must be on or after start date.")
            if end > date.today():
                raise ValidationError("End date cannot be in the future.")
        return cleaned

class FetchWeatherForm(forms.Form):
    location_search = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Type a city name e.g. New Delhi, London…',
            'id':          'locationSearch',
            'autocomplete':'off',
        })
    )
    # Hidden fields — filled automatically by JavaScript when user picks a city
    latitude = forms.DecimalField(
        max_digits=9, decimal_places=6,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLat'})
    )
    longitude = forms.DecimalField(
        max_digits=9, decimal_places=6,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLon'})
    )
    location_name = forms.CharField(
        max_length=255,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLocationName'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type':  'date',
            'class': 'form-control',
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type':  'date',
            'class': 'form-control',
        })
    )

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get('start_date')
        end     = cleaned.get('end_date')
        lat     = cleaned.get('latitude')
        lon     = cleaned.get('longitude')

        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date.")
        if not lat or not lon:
            raise forms.ValidationError("Please select a valid city from the suggestions.")
        return cleaned


class FetchForecastForm(forms.Form):
    location_search = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Type a city name e.g. Mumbai, Berlin…',
            'id':          'locationSearchForecast',
            'autocomplete':'off',
        })
    )
    # Hidden fields — filled automatically by JavaScript
    latitude = forms.DecimalField(
        max_digits=9, decimal_places=6,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLatForecast'})
    )
    longitude = forms.DecimalField(
        max_digits=9, decimal_places=6,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLonForecast'})
    )
    location_name = forms.CharField(
        max_length=255,
        widget=forms.HiddenInput(attrs={'id': 'hiddenLocationNameForecast'})
    )
    forecast_days = forms.IntegerField(
        min_value=1,
        max_value=16,
        initial=7,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min':   '1',
            'max':   '16',
        })
    )

    def clean(self):
        cleaned = super().clean()
        lat     = cleaned.get('latitude')
        lon     = cleaned.get('longitude')
        days    = cleaned.get('forecast_days')

        if not lat or not lon:
            raise forms.ValidationError("Please select a valid city from the suggestions.")
        if days and (days < 1 or days > 16):
            raise forms.ValidationError("Forecast days must be between 1 and 16.")
        return cleaned