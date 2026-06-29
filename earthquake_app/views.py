"""
earthquake_app/views.py
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max

from .models import AppUser, Earthquake
from .forms  import LoginForm, RegisterForm, FetchDataForm
from .usgs_fetcher import fetch_and_store


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