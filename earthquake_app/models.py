"""
earthquake_app/models.py
Database models for the Earthquake Monitoring System.

Tables created:
  - app_user        (custom user authentication)
  - earthquake      (USGS earthquake data)
"""
from django.db import models
from django.utils import timezone
import hashlib
import os


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM USER MODEL
# We manage our own users table (not Django's built-in auth_user).
# ─────────────────────────────────────────────────────────────────────────────
class AppUser(models.Model):
    """
    Custom user table stored as `app_user` in MySQL.

    Columns:
        user_id    INT AUTO_INCREMENT PRIMARY KEY
        username   VARCHAR(150) UNIQUE
        password   VARCHAR(255)  — SHA-256 hashed with salt
        email      VARCHAR(254) UNIQUE
        created_at DATETIME
    """
    user_id    = models.AutoField(primary_key=True)
    username   = models.CharField(max_length=150, unique=True)
    # Stored as  salt:sha256hash  so we can verify without plain text
    password   = models.CharField(max_length=255)
    email      = models.EmailField(max_length=254, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "app_user"
        ordering = ["-created_at"]

    # ── Password helpers ──────────────────────────────────────────────────

    @staticmethod
    def hash_password(plain_text: str) -> str:
        """Return  salt:sha256(salt+password)  string."""
        salt = os.urandom(16).hex()          # 32-char random hex salt
        hashed = hashlib.sha256((salt + plain_text).encode()).hexdigest()
        return f"{salt}:{hashed}"

    def set_password(self, plain_text: str):
        """Hash and store a plain-text password."""
        self.password = self.hash_password(plain_text)

    def check_password(self, plain_text: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        try:
            salt, stored_hash = self.password.split(":", 1)
            candidate = hashlib.sha256((salt + plain_text).encode()).hexdigest()
            return candidate == stored_hash
        except ValueError:
            return False

    def __str__(self):
        return f"{self.username} ({self.email})"


# ─────────────────────────────────────────────────────────────────────────────
# EARTHQUAKE MODEL
# ─────────────────────────────────────────────────────────────────────────────
class Earthquake(models.Model):
    """
    Stores filtered USGS earthquake data.

    The USGS feature `id` (e.g. "us7000mfgl") is used as the natural
    primary key — this automatically prevents duplicate inserts.

    Columns:
        earthquake_id  VARCHAR(20)  PRIMARY KEY
        magnitude      DECIMAL(4,2)
        place          VARCHAR(300)
        time           DATETIME
        latitude       DECIMAL(10,6)
        longitude      DECIMAL(10,6)
        depth          DECIMAL(10,3)   (kilometres)
        url            VARCHAR(512)
        fetched_at     DATETIME        (when we pulled this record)
    """
    earthquake_id = models.CharField(max_length=20, primary_key=True)
    magnitude     = models.DecimalField(max_digits=4,  decimal_places=2)
    place         = models.CharField(max_length=300, null=True, blank=True)
    time          = models.DateTimeField(null=True, blank=True)
    latitude      = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    longitude     = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    depth         = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    url           = models.CharField(max_length=512, null=True, blank=True)
    fetched_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "earthquake"
        ordering = ["-time"]

    def __str__(self):
        return f"M{self.magnitude} – {self.place} ({self.time})"
    
# ─────────────────────────────────────────────────────────────────────────────
# WEATHER RECORD MODEL
# ─────────────────────────────────────────────────────────────────────────────
class WeatherRecord(models.Model):
    DATA_TYPE_CHOICES = [
        ("historical", "Historical"),
        ("forecast",   "Forecast"),
    ]

    location_name     = models.CharField(max_length=255, null=True, blank=True)
    latitude          = models.DecimalField(max_digits=9,  decimal_places=6)
    longitude         = models.DecimalField(max_digits=9,  decimal_places=6)
    date              = models.DateField()
    temperature_max   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature_min   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precipitation_sum = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    data_type         = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, default="historical")
    fetched_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "weather_record"
        unique_together = ('latitude', 'longitude', 'date', 'data_type')
        ordering        = ['-date']

    def __str__(self):
        return f"{self.date} | {self.location_name or f'{self.latitude},{self.longitude}'} ({self.data_type})"
