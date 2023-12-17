from typing import Any
from asgiref.sync import sync_to_async
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import generic, View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.forms.widgets import TextInput
from django.contrib import messages
from extra_views import ModelFormSetView
from lynx import url_parser, url_summarizer, html_cleaner
from lynx.models import Link, UserSetting, UserCookie
from lynx.errors import NoAPIKeyInSettings
import secrets


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


class SummarizeLinkView(View):

  async def post(self, request, pk):
    try:
      if not await (sync_to_async(lambda: request.user.is_authenticated)()):
        return JsonResponse(
            {"error": "You must be logged in to summarize a link."})
      link = await Link.objects.aget(pk=pk, creator=request.user)
      link = await url_summarizer.generate_and_persist_summary(link)

      return HttpResponseRedirect(
          reverse("lynx:link_details", args=(link.pk, )))
    except Link.DoesNotExist:
      return JsonResponse({"error": "Link does not exist."})
    except NoAPIKeyInSettings:
      return JsonResponse(
          {"error": "You must have an OpenAI API key in your settings."})


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

  def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
    data = super().get_context_data(**kwargs)
    cleaner = html_cleaner.HTMLCleaner(data['link'].article_html)
    cleaner.generate_headings().replace_image_links_with_images()
    data['html_with_sections'] = cleaner.prettify()
    data['table_of_contents'] = [h.to_dict() for h in cleaner.get_headings()]
    return data


class DetailsView(LoginRequiredMixin, generic.DetailView):
  model = Link
  template_name = "lynx/link_details.html"

  def get_queryset(self):
    return Link.objects.filter(creator=self.request.user)


class FeedView(LoginRequiredMixin, generic.ListView):
  template_name = "lynx/links_feed.html"
  context_object_name = "links_list"
  paginate_by = 25
  filter = None

  def get_queryset(self):
    query_string = self.request.GET.get('q', '')
    if query_string:
      sql = '''
        SELECT lynx_link.*, rank 
        FROM lynx_link 
        INNER JOIN (
          SELECT rowid, rank 
          FROM lynx_link_fts 
          WHERE lynx_link_fts MATCH %s
        ) 
        ON lynx_link.id = rowid 
        ORDER BY rank;
      '''
      return Link.objects.raw(sql, [query_string])
    else:
      queryset = Link.objects.filter(creator=self.request.user)
      if self.filter == "read":
        queryset = queryset.filter(last_viewed_at__isnull=False)
      elif self.filter == "unread":
        queryset = queryset.filter(last_viewed_at__isnull=True)

      return queryset.order_by('-created_at')

  def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
    data = super().get_context_data(**kwargs)
    data['selected_filter'] = self.filter
    data['query'] = self.request.GET.get('q', '')

    if self.filter == "read":
      data['title'] = "Read Links"
    elif self.filter == "unread":
      data['title'] = "Unread Links"
    elif self.filter == "search":
      data['title'] = "Search Results"
    else:
      data['title'] = "All Links"

    return data


class APIKeyWidget(TextInput):
  template_name = "widgets/api_key_widget.html"


class UpdateSettingsForm(forms.Form):
  openai_api_key = forms.CharField(
      label="OpenAI API Key",
      max_length=255,
      widget=forms.PasswordInput(render_value=True),
      required=False)

  lynx_api_key = forms.CharField(
      label="Lynx API Key",
      max_length=255,
      required=False,
      widget=APIKeyWidget(),
  )

  def update_setting(self, user):
    setting, _ = UserSetting.objects.get_or_create(user=user)
    if 'reset_api_key' in self.data:
      setting.lynx_api_key = secrets.token_hex(16)
    elif 'clear_api_key' in self.data:
      setting.lynx_api_key = ""
    setting.save()


class UpdateSettingsView(LoginRequiredMixin, generic.FormView):
  template_name = 'lynx/usersetting_form.html'
  form_class = UpdateSettingsForm

  def form_valid(self, form):
    form.update_setting(self.request.user)
    messages.success(self.request, "Settings updated.")
    return HttpResponseRedirect(reverse("lynx:user_settings"))

  def get_initial(self):
    setting, _ = UserSetting.objects.get_or_create(user=self.request.user)
    initial = super().get_initial()
    initial['openai_api_key'] = setting.openai_api_key
    initial['lynx_api_key'] = setting.lynx_api_key
    return initial


class UpdateCookiesView(LoginRequiredMixin, ModelFormSetView):
  model = UserCookie
  fields = ["user", "cookie_name", "cookie_value", "cookie_domain"]
  template_name = 'lynx/usercookie_form.html'

  def get_factory_kwargs(self):
    args = super().get_factory_kwargs()
    args['can_delete'] = True
    args['can_delete_extra'] = False
    args['widgets'] = {
        'user': forms.HiddenInput(),
        'cookie_value': forms.PasswordInput(render_value=True),
    }
    return args

  def get_formset(self):
    formset = super().get_formset()
    formset.deletion_widget = forms.CheckboxInput(attrs={'role': 'switch'})
    return formset

  def get_initial(self):
    return [{
        'user': self.request.user,
    }]

  def get_queryset(self):
    return UserCookie.objects.filter(user=self.request.user)
