from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from django.utils import timezone
from lynx import url_parser
from lynx.models import Link


def index(request):
    return HttpResponse("Hello, world.")

def test_parse(request):
  parsed_url = url_parser.parse_url('https://github.blog/2019-03-29-leader-spotlight-erin-spiceland')
  return HttpResponse("The parsed URL author is: " + str(parsed_url.get_author()))

class ReadableView(generic.DetailView):
  model = Link
  template_name = "lynx/link_viewer.html"
  def get_object(self):
    obj = super().get_object()
    obj.last_viewed_at = timezone.now()
    obj.save()
    return obj

class DetailsView(generic.DetailView):
  model = Link
  template_name = "lynx/link_details.html"

class FeedView(generic.ListView):
  model = Link
  template_name = "lynx/links_feed.html"
  context_object_name = "links_list"
  paginate_by = 40