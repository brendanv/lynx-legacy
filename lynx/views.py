from django.http import HttpResponse
from django.shortcuts import render
from lynx import url_parser


def index(request):
    return HttpResponse("Hello, world.")

def readable(request, link_id):
  return render(request, "lynx/readable_link.html", {"link_id": link_id})
  
def test_parse(request):
  parsed_url = url_parser.parse_url('https://github.blog/2019-03-29-leader-spotlight-erin-spiceland')
  return HttpResponse("The parsed URL author is: " + str(parsed_url.get_author()))