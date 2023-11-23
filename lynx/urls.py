from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'lynx'
urlpatterns = [
    path("", views.index, name="index"),
    path("links/all",
         login_required(views.FeedView.as_view(), login_url='/admin'),
         name="links_feed"),
    path("link/<int:pk>/details/",
         views.DetailsView.as_view(),
         name="link_details"),
    path("link/<int:pk>/view",
         views.ReadableView.as_view(),
         name="link_viewer"),
    path("links/add",
         login_required(views.add_link, login_url='/admin'),
         name="add_link"),
    path("links/create",
         login_required(views.create_link, login_url='/admin'),
         name="create_link")
]
