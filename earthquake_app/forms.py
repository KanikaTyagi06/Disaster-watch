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
