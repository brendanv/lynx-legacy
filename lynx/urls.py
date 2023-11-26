from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    path("",
         views.FeedView.as_view(),
         name="links_feed"),
    path("<int:pk>/details/",
         views.DetailsView.as_view(),
         name="link_details"),
    path("<int:pk>/view",
         views.ReadableView.as_view(),
         name="link_viewer"),
    path("add/",
         views.AddLinkView.as_view(),
         name="add_link"),
    path("<int:pk>/summarize/",
         views.SummarizeLinkView.as_view(),
         name="summarize_link"),
    path('settings/',
         views.UpdateSettingsView.as_view(),
         name='user_settings'),
]
