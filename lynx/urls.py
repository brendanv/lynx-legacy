from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    # Feed
    path("", views.LinkFeedView.as_view(filter="all"), name="links_feed"),
    path("all/",
         views.LinkFeedView.as_view(filter="all"),
         name="links_feed_all"),
    path("unread/",
         views.LinkFeedView.as_view(filter="unread"),
         name="links_feed_unread"),
    path("read/",
         views.LinkFeedView.as_view(filter="read"),
         name="links_feed_read"),
    path("search/",
         views.LinkFeedView.as_view(filter="search"),
         name="links_feed_search"),

    # Link views + actions
    path("<int:pk>/details/", views.DetailsView.as_view(),
         name="link_details"),
    path("<int:pk>/view", views.ReadableView.as_view(), name="link_viewer"),
    path("add/", views.AddLinkView.as_view(), name="add_link"),
    path("<int:pk>/summarize/",
         views.SummarizeLinkView.as_view(),
         name="summarize_link"),

    # Feed views
    path("feeds/", views.FeedListView.as_view(), name="feeds"),
    path("feeds/refresh_all/",
         views.RefreshAllFeedsView.as_view(),
         name="refresh_all_feeds"),
    path("feeds/add/", views.AddFeedView.as_view(), name="add_feed"),
    path("feeds/<int:feed_id>/items/",
         views.FeedItemListView.as_view(),
         name="feed_items"),
    path("feeds/<int:pk>/refresh/",
         views.RefreshFeedFromRemoteView.as_view(),
         name="refresh_feed"),
    path("feed_item/<int:pk>/add_to_library/",
         views.AddFeedItemToLibraryView.as_view(),
         name="add_feed_item_to_library"),

    # User settings
    path('settings/', views.UpdateSettingsView.as_view(),
         name='user_settings'),
    path('cookies/', views.UpdateCookiesView.as_view(), name='user_cookies'),
]
