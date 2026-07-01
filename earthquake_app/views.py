"""
earthquake_app/views.py
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
import json
from django.http import JsonResponse

from .models import AppUser, Earthquake, WeatherRecord
from .forms  import LoginForm, RegisterForm, FetchDataForm, FetchWeatherForm, FetchForecastForm
from .usgs_fetcher import fetch_and_store
from .open_meteo_fetcher import fetch_and_store_weather, fetch_and_store_forecast
from .geocoding_fetcher import search_locations


def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            messages.warning(request, "Please log in to access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.session.get("user_id"):
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        try:
            user = AppUser.objects.get(username=username)
            if user.check_password(password):
                request.session["user_id"]  = user.user_id
                request.session["username"] = user.username
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
        except AppUser.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, "earthquake_app/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    return redirect("login")


def register_view(request):
    if request.session.get("user_id"):
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        email    = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        if AppUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif AppUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            user = AppUser(username=username, email=email)
            user.set_password(password)
            user.save()
            messages.success(request, "Account created! Please log in.")
            return redirect("login")

    return render(request, "earthquake_app/register.html", {"form": form})


@login_required_custom
def dashboard_view(request):
    total_earthquakes = Earthquake.objects.count()
    total_users       = AppUser.objects.count()
    strongest         = Earthquake.objects.order_by("-magnitude").first()
    latest            = Earthquake.objects.order_by("-time").first()
    last_fetch        = Earthquake.objects.aggregate(last=Max("fetched_at"))["last"]

    mag_ranges = {
        "range1": Earthquake.objects.filter(magnitude__gte=6.0, magnitude__lt=6.5).count(),
        "range2": Earthquake.objects.filter(magnitude__gte=6.5, magnitude__lt=7.0).count(),
        "range3": Earthquake.objects.filter(magnitude__gte=7.0, magnitude__lt=7.5).count(),
        "range4": Earthquake.objects.filter(magnitude__gte=7.5, magnitude__lt=8.0).count(),
        "range5": Earthquake.objects.filter(magnitude__gte=8.0).count(),
    }
    recent = Earthquake.objects.order_by("-time")[:5]

    return render(request, "earthquake_app/dashboard.html", {
        "total_earthquakes": total_earthquakes,
        "total_users":       total_users,
        "strongest":         strongest,
        "latest":            latest,
        "last_fetch":        last_fetch,
        "mag_ranges":        mag_ranges,
        "recent":            recent,
        "username":          request.session.get("username"),
    })


@login_required_custom
def earthquakes_view(request):
    qs = Earthquake.objects.all()

    search    = request.GET.get("search", "").strip()
    mag_min   = request.GET.get("mag_min", "")
    mag_max   = request.GET.get("mag_max", "")
    date_from = request.GET.get("date_from", "")
    date_to   = request.GET.get("date_to", "")
    sort_by   = request.GET.get("sort", "-time")

    if search:
        qs = qs.filter(Q(place__icontains=search) | Q(earthquake_id__icontains=search))
    if mag_min:
        try: qs = qs.filter(magnitude__gte=float(mag_min))
        except ValueError: pass
    if mag_max:
        try: qs = qs.filter(magnitude__lte=float(mag_max))
        except ValueError: pass
    if date_from:
        qs = qs.filter(time__date__gte=date_from)
    if date_to:
        qs = qs.filter(time__date__lte=date_to)

    allowed_sorts = ["time","-time","magnitude","-magnitude","place","-place","depth","-depth"]
    if sort_by not in allowed_sorts:
        sort_by = "-time"
    qs = qs.order_by(sort_by)

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    return render(request, "earthquake_app/earthquakes.html", {
        "page_obj":  page_obj,
        "search":    search,
        "mag_min":   mag_min,
        "mag_max":   mag_max,
        "date_from": date_from,
        "date_to":   date_to,
        "sort_by":   sort_by,
        "total":     qs.count(),
        "username":  request.session.get("username"),
    })


@login_required_custom
def fetch_view(request):
    form   = FetchDataForm()
    result = None

    if request.method == "POST":
        form = FetchDataForm(request.POST)
        if form.is_valid():
            start = str(form.cleaned_data["start_date"])
            end   = str(form.cleaned_data["end_date"])
            try:
                result = fetch_and_store(start, end)
                if result["errors"]:
                    for err in result["errors"]:
                        messages.error(request, err)
                elif result["filtered"] == 0:
                    messages.info(request, "No earthquakes ≥ 6.0 found in this date range.")
                else:
                    messages.success(
                        request,
                        f"✅ Fetch complete! Inserted {result['inserted']} new record(s), "
                        f"skipped {result['skipped']} duplicate(s)."
                    )
            except Exception as e:
                messages.error(request, f"Unexpected error: {e}")

    return render(request, "earthquake_app/fetch.html", {
        "form":     form,
        "result":   result,
        "username": request.session.get("username"),
    })

# ─────────────────────────────────────────────────────────────────────────────
# WEATHER VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@login_required_custom
def geocode_search_view(request):
    """
    AJAX endpoint — returns matching city list as JSON.
    Called by the city search box in weather fetch forms.
    GET /api/geocode/search/?q=delhi
    """
    query   = request.GET.get("q", "").strip()
    results = search_locations(query) if len(query) >= 2 else []
    return JsonResponse({"results": results})


@login_required_custom
def weather_fetch_view(request):
    form   = FetchWeatherForm()
    result = None

    if request.method == "POST":
        form = FetchWeatherForm(request.POST)
        if form.is_valid():
            result = fetch_and_store_weather(
                start_date=str(form.cleaned_data["start_date"]),
                end_date=str(form.cleaned_data["end_date"]),
                latitude=form.cleaned_data["latitude"],
                longitude=form.cleaned_data["longitude"],
                location_name=form.cleaned_data["location_name"],
            )
            if result["errors"]:
                for err in result["errors"]:
                    messages.error(request, err)
            elif result["inserted"] == 0 and result["skipped"] == 0:
                messages.info(request, "No data returned from API for this range.")
            else:
                messages.success(
                    request,
                    f"✅ Fetch complete! Inserted {result['inserted']} new record(s), "
                    f"skipped {result['skipped']} duplicate(s)."
                )

    return render(request, "earthquake_app/weather_fetch.html", {
        "form":     form,
        "result":   result,
        "username": request.session.get("username"),
    })


@login_required_custom
def weather_forecast_fetch_view(request):
    form   = FetchForecastForm()
    result = None

    if request.method == "POST":
        form = FetchForecastForm(request.POST)
        if form.is_valid():
            result = fetch_and_store_forecast(
                latitude=form.cleaned_data["latitude"],
                longitude=form.cleaned_data["longitude"],
                forecast_days=form.cleaned_data["forecast_days"],
                location_name=form.cleaned_data["location_name"],
            )
            if result["errors"]:
                for err in result["errors"]:
                    messages.error(request, err)
            elif result["inserted"] == 0 and result["skipped"] == 0:
                messages.info(request, "No forecast data returned from API.")
            else:
                messages.success(
                    request,
                    f"✅ Forecast fetched! Inserted {result['inserted']} new record(s), "
                    f"skipped {result['skipped']} duplicate(s)."
                )

    return render(request, "earthquake_app/weather_forecast.html", {
        "form":     form,
        "result":   result,
        "username": request.session.get("username"),
    })


@login_required_custom
def weather_view(request):
    qs        = WeatherRecord.objects.all()
    date_from = request.GET.get("date_from",  "")
    date_to   = request.GET.get("date_to",    "")
    location  = request.GET.get("location",   "")
    data_type = request.GET.get("data_type",  "")
    sort_by   = request.GET.get("sort",       "-date")
    latitude  = request.GET.get("latitude",   "")
    longitude = request.GET.get("longitude",  "")
    auto_fetched = False
    fetch_result = None

    # ── Smart Auto-Fetch Logic ──────────────────────────────────────────
    # Agar user ne location + dates + lat/lon diya hai aur DB mein data
    # nahi hai toh automatically API se fetch karke save karo
    if latitude and longitude and date_from and date_to and data_type in ("historical", "forecast"):
        existing = WeatherRecord.objects.filter(
            latitude=latitude,
            longitude=longitude,
            date__gte=date_from,
            date__lte=date_to,
            data_type=data_type,
        ).exists()

        if not existing:
            try:
                if data_type == "historical":
                    fetch_result = fetch_and_store_weather(
                        start_date=date_from,
                        end_date=date_to,
                        latitude=latitude,
                        longitude=longitude,
                        location_name=location,
                    )
                else:
                    from datetime import date, timedelta
                    today     = date.today()
                    end_date  = date_to if date_to else str(today + timedelta(days=7))
                    days_diff = (date.fromisoformat(end_date) - today).days + 1
                    days_diff = max(1, min(days_diff, 16))
                    fetch_result = fetch_and_store_forecast(
                        latitude=latitude,
                        longitude=longitude,
                        forecast_days=days_diff,
                        location_name=location,
                    )
                auto_fetched = True
            except Exception as e:
                messages.error(request, f"Auto-fetch error: {e}")

    # ── Filter DB records ───────────────────────────────────────────────
    if date_from:  qs = qs.filter(date__gte=date_from)
    if date_to:    qs = qs.filter(date__lte=date_to)
    if location:   qs = qs.filter(location_name__icontains=location)
    if latitude:   qs = qs.filter(latitude=latitude)
    if longitude:  qs = qs.filter(longitude=longitude)
    if data_type in ("historical", "forecast"):
        qs = qs.filter(data_type=data_type)

    allowed_sorts = [
        "date", "-date",
        "temperature_max", "-temperature_max",
        "precipitation_sum", "-precipitation_sum",
    ]
    if sort_by not in allowed_sorts:
        sort_by = "-date"
    qs = qs.order_by(sort_by)

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get("page"))

    return render(request, "earthquake_app/weather.html", {
        "page_obj":     page_obj,
        "total":        qs.count(),
        "date_from":    date_from,
        "date_to":      date_to,
        "location":     location,
        "data_type":    data_type,
        "sort_by":      sort_by,
        "latitude":     latitude,
        "longitude":    longitude,
        "auto_fetched": auto_fetched,
        "fetch_result": fetch_result,
        "username":     request.session.get("username"),
    })