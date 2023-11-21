from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse("Hello, world.")

def readable(request, link_id):
  return render(request, "lynx/readable_link.html", {"link_id": link_id})