from django import forms
from django.forms.widgets import TextInput

class APIKeyWidget(TextInput):
  template_name = "widgets/api_key_widget.html"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.attrs['readonly'] = ''


class FancyTextWidget(TextInput):
  template_name = "widgets/fancy_text_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['display_name'] = display_name


class FancyPasswordWidget(forms.PasswordInput):
  template_name = "widgets/fancy_password_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['display_name'] = display_name
    self.attrs['autocomplete'] = 'off'

