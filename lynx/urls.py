from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    path("", views.index, name="index"),
    path("links/all", views.FeedView.as_view(), name="links_feed"),
    path("link/<int:pk>/details/", views.DetailsView.as_view(), name="link_details"),
    path("link/<int:pk>/view", views.ReadableView.as_view(), name="link_viewer"),
    path("test_parse", views.test_parse, name="test_parse")
]
