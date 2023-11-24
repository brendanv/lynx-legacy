from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import reverse, render, redirect
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from lynx import url_parser
from lynx.models import Link


def index(request):
  return HttpResponse("Hello, world.")


class AddLinkForm(forms.Form):
  url = forms.URLField(label="URL", max_length=2000)

  def create_link(self, user):
    url = url_parser.parse_url(self.cleaned_data['url'], user)
    url.save()
    return url


class AddLinkView(LoginRequiredMixin, generic.FormView):
  template_name = 'lynx/add_link.html'
  form_class = AddLinkForm

  def form_valid(self, form):
    link = form.create_link(self.request.user)
    return HttpResponseRedirect(reverse("lynx:link_viewer", args=(link.id, )))


class ReadableView(LoginRequiredMixin, generic.DetailView):
  model = Link
  template_name = "lynx/link_viewer.html"

  def get_queryset(self):
    return Link.objects.filter(creator=self.request.user)

  def get_object(self):
    obj = super().get_object()
    obj.last_viewed_at = timezone.now()
    obj.save()
    return obj


class DetailsView(LoginRequiredMixin, generic.DetailView):
  model = Link
  template_name = "lynx/link_details.html"

  def get_queryset(self):
    return Link.objects.filter(creator=self.request.user)


class FeedView(LoginRequiredMixin, generic.ListView):
  template_name = "lynx/links_feed.html"
  context_object_name = "links_list"
  paginate_by = 25

  def get_queryset(self):
    return Link.objects.filter(
        creator=self.request.user).order_by('-created_at')
