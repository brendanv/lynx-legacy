from django.urls import path

from . import views

app_name = 'lynx'
urlpatterns = [
    # Feed
    path("", 
         views.link_feed_view, {'filter': 'all'},
         name="links_feed"),
    path("all/",
         views.link_feed_view, {'filter': 'all'},
         name="links_feed_all"),
    path("unread/",
         views.link_feed_view, {'filter': 'unread'},
         name="links_feed_unread"),
    path("read/",
         views.link_feed_view, {'filter': 'read'},
         name="links_feed_read"),
    path("search/",
         views.link_feed_view, {'filter': 'search'},
         name="links_feed_search"),

    # Link views + actions
    path("<int:pk>/details/", views.details_view,
         name="link_details"),
    path("<int:pk>/view", views.readable_view, name="link_viewer"),
    path("add/", views.add_link_view, name="add_link"),
    path("<int:pk>/summarize/",
         views.summarize_link_view,
         name="summarize_link"),

    # Feed views
    path("feeds/", views.feeds_list_view, name="feeds"),
    path("feeds/refresh_all/",
         views.refresh_all_feeds_view,
         name="refresh_all_feeds"),
    path("feeds/add/", views.add_feed_view, name="add_feed"),
    path("feeds/<int:feed_id>/items/",
         views.feed_items_list_view,
         name="feed_items"),
    path("feeds/<int:pk>/refresh/",
         views.refresh_feed_from_remote_view,
         name="refresh_feed"),
    path("feed_item/<int:pk>/add_to_library/",
         views.add_feed_item_to_library_view,
         name="add_feed_item_to_library"),

    # User settings
    path('settings/', views.update_settings_view, name='user_settings'),
    path('cookies/', views.UpdateCookiesView.as_view(), name='user_cookies'),
]
