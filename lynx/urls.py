from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("link/<int:link_id>", views.readable, name="readable")
]