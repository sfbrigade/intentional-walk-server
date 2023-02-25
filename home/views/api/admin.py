import json

from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.views import View

class AdminMeView(View):
  http_method_names = ["get"]

  def get(self, request, *args, **kwargs):
    if request.user.is_authenticated:      
      return JsonResponse(model_to_dict(request.user))
    else:
      return HttpResponse(status=204)
