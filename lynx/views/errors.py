from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

def page_not_found(request: HttpRequest, exception) -> HttpResponse:
  return TemplateResponse(request, 'lynx/404.html', status=404)
  
def internal_error(request: HttpRequest) -> HttpResponse:
  return TemplateResponse(request, 'lynx/500.html', status=500)
  