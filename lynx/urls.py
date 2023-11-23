from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    path("", views.index, name="index"),
    path("links/all", views.FeedView.as_view(), name="links_feed"),
    path("link/<int:pk>/details/", views.DetailsView.as_view(), name="link_details"),
    path("link/<int:pk>/view", views.ReadableView.as_view(), name="link_viewer"),
    path("links/add", views.add_link, name="add_link"),
    path("links/create", views.create_link, name="create_link")
]
