from django import forms
from django.forms.widgets import TextInput, DateInput

class APIKeyWidget(TextInput):
  template_name = "widgets/api_key_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['readonly'] = ''
    self.attrs['display_name'] = display_name


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

class FancyDateWidget(DateInput):
  template_name = "widgets/fancy_date_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['display_name'] = display_name
    self.attrs['type'] = 'date'

class DaisySelect(forms.Select):
  template_name = "widgets/daisy_select.html"

