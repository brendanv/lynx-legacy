from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import reverse, render, redirect
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from lynx import url_parser
from lynx.models import Link


def index(request):
  return HttpResponse("Hello, world.")

def add_link(request):
  return render(request, "lynx/add_link.html")

@require_http_methods(["POST"])
def create_link(request):
  url = request.POST.get("url")
  print(url)
  if url:
    parsed_url = url_parser.parse_url(url)
    parsed_url.save()
    print(parsed_url)
    return HttpResponseRedirect(
        reverse("lynx:link_viewer", args=(parsed_url.id, )))
  else:
    return render(request, "lynx/add_link.html",
                  {"error_message": "URL is required."})


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
