from .decorators import async_login_required
from .widgets import FancyTextWidget, FancyPasswordWidget, APIKeyWidget
from asgiref.sync import sync_to_async
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.contrib import messages
from extra_views import ModelFormSetView
from lynx.models import UserSetting, UserCookie
import secrets
from django.shortcuts import redirect

class UpdateSettingsForm(forms.Form):
  openai_api_key = forms.CharField(label="",
                                   max_length=255,
                                   widget=FancyPasswordWidget(
                                       'OpenAI API Key', render_value=True),
                                   required=False)

  lynx_api_key = forms.CharField(
      label="",
      max_length=255,
      required=False,
      widget=APIKeyWidget('Lynx API Key'),
  )

  def update_setting(self, user):
    setting, _ = UserSetting.objects.get_or_create(user=user)
    if 'reset_api_key' in self.data:
      setting.lynx_api_key = secrets.token_hex(16)
    elif 'clear_api_key' in self.data:
      setting.lynx_api_key = ""
    setting.save()


@async_login_required
async def update_settings_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  setting, _ = await UserSetting.objects.aget_or_create(user=user)
  if request.method == 'POST':
    form = UpdateSettingsForm(request.POST)
    if form.is_valid():
      await (sync_to_async(lambda: form.update_setting(user))())
      messages.success(request, "Settings updated.")
      return redirect('lynx:user_settings')
  else:
    form = UpdateSettingsForm(
        initial={
            'openai_api_key': setting.openai_api_key,
            'lynx_api_key': setting.lynx_api_key,
        })

  return TemplateResponse(request, "lynx/usersetting_form.html",
                          {'form': form})


class UpdateCookiesView(LoginRequiredMixin, ModelFormSetView):
  model = UserCookie
  fields = ["user", "cookie_name", "cookie_value", "cookie_domain"]
  template_name = 'lynx/usercookie_form.html'

  def get_factory_kwargs(self):
    args = super().get_factory_kwargs()
    args['can_delete'] = True
    args['can_delete_extra'] = False
    args['labels'] = {
        'cookie_name': '',
        'cookie_value': '',
        'cookie_domain': ''
    }
    args['widgets'] = {
        'user':
        forms.HiddenInput(),
        'cookie_value':
        FancyPasswordWidget('Cookie Value', render_value=True),
        'cookie_name':
        FancyTextWidget('Cookie Name', attrs={'autocomplete': 'off'}),
        'cookie_domain':
        FancyTextWidget('Cookie Domain', attrs={'autocomplete': 'off'}),
    }
    return args

  def get_formset(self):
    formset = super().get_formset()
    formset.deletion_widget = forms.CheckboxInput(
        attrs={'class': 'checkbox checkbox-primary'})
    return formset

  def get_initial(self):
    return [{
        'user': self.request.user,
    }]

  def get_queryset(self):
    return UserCookie.objects.filter(user=self.request.user)

