"""
earthquake_app/urls.py  –  Web (HTML) URL routes.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("",             views.login_view,      name="home"),
    path("login/",       views.login_view,      name="login"),
    path("logout/",      views.logout_view,     name="logout"),
    path("register/",    views.register_view,   name="register"),
    path("dashboard/",   views.dashboard_view,  name="dashboard"),
    path("earthquakes/", views.earthquakes_view, name="earthquakes"),
    path("fetch/",       views.fetch_view,      name="fetch"),
]
