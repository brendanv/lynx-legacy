from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    # Feed
    path("", views.FeedView.as_view(filter="all"), name="links_feed"),
    path("all/", views.FeedView.as_view(filter="all"), name="links_feed_all"),
    path("unread/",
         views.FeedView.as_view(filter="unread"),
         name="links_feed_unread"),
    path("read/",
         views.FeedView.as_view(filter="read"),
         name="links_feed_read"),
    path("search/",
         views.FeedView.as_view(filter="search"),
         name="links_feed_search"),

    # Link views + actions
    path("<int:pk>/details/", views.DetailsView.as_view(),
         name="link_details"),
    path("<int:pk>/view", views.ReadableView.as_view(), name="link_viewer"),
    path("add/", views.AddLinkView.as_view(), name="add_link"),
    path("<int:pk>/summarize/",
         views.SummarizeLinkView.as_view(),
         name="summarize_link"),

    # User settings
    path('settings/', views.UpdateSettingsView.as_view(),
         name='user_settings'),
]
