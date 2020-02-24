from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from .models import AppUser, DailyWalk, IntentionalWalk


@method_decorator(csrf_exempt, name='dispatch')
class AppUserCreateView(View):
    model = AppUser
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # Yank out all the attributes
        name = request.POST.get("name")
        email = request.POST.get("email")
        zip = request.POST.get("zip")
        age = request.POST.get("age")
        device_id = request.POST.get("device_id")

        # If any of the field is missing, return an error
        if name is None:
            return JsonResponse({"status": "error", "message": "Name missing"})
        if email is None:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if zip is None:
            return JsonResponse({"status": "error", "message": "Zip missing"})
        if age is None:
            return JsonResponse({"status": "error", "message": "Age missing"})
        if device_id is None:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        # Update if the object exists else create
        try:
            appuser = AppUser.objects.get(email=email, device_id=device_id)
            appuser.name = name
            appuser.zip = zip
            appuser.age = age
            appuser.save()
            return JsonResponse({"status": "success", "message": "App User updated successfully"})

        except ObjectDoesNotExist:
            obj = AppUser.objects.create(name=name,
                                 email=email,
                                 zip=zip,
                                 age=age,
                                 device_id=device_id)

            return JsonResponse({"status": "success", "message": "App User registered successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class DailyWalkView(View):
    model = DailyWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        device_id = request.POST.get("device_id")
        date = request.POST.get("date")
        steps = request.POST.get("steps")

        # If any of the field is missing, return an error
        if email is None:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if device_id is None:
            return JsonResponse({"status": "error", "message": "Device_id missing"})
        if date is None:
            return JsonResponse({"status": "error", "message": "Date missing"})
        if steps is None:
            return JsonResponse({"status": "error", "message": "Steps missing"})

        try:
            user = AppUser.objects.get(email=email, device_id=device_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        try:
            _ = DailyWalk.objects.get(user=user, date=date)
            return JsonResponse({"status": "error", "message": "Steps already entered for this date"})
        except ObjectDoesNotExist:
            _ = DailyWalk.objects.create(date=date,
                                           steps=steps,
                                           user=user)

            return JsonResponse({"status": "success", "message": "Daily Walk recorded successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class DailyWalkListView(View):
    model = DailyWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        device_id = request.POST.get("device_id")

        # If any of the field is missing, return an error
        if email is None:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if device_id is None:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        try:
            user = AppUser.objects.get(email=email, device_id=device_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        daily_walks = DailyWalk.objects.filter(user=user)
        # Hacky serializer
        total_steps = 0
        daily_walk_list = []
        for daily_walk in daily_walks:
            daily_walk_list.append({
                "date": daily_walk.date,
                "steps": daily_walk.steps
            })
            total_steps+=daily_walk.steps

        payload = {
            "daily_walks": daily_walk_list,
            "total_steps": total_steps
        }

        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class IntentionalWalkView(View):
    model = IntentionalWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        device_id = request.POST.get("device_id")
        start = request.POST.get("start")
        end = request.POST.get("end")
        steps = request.POST.get("steps")

        # If any of the field is missing, return an error
        if email is None:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if device_id is None:
            return JsonResponse({"status": "error", "message": "Device_id missing"})
        if start is None:
            return JsonResponse({"status": "error", "message": "Start timestamp missing"})
        if end is None:
            return JsonResponse({"status": "error", "message": "End timestamp missing"})
        if steps is None:
            return JsonResponse({"status": "error", "message": "Steps missing"})

        try:
            user = AppUser.objects.get(email=email, device_id=device_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        _ = IntentionalWalk.objects.create(start=start,
                                             end=end,
                                             steps=steps,
                                             user=user)

        return JsonResponse({"status": "success", "message": "Intentional Walk recorded successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class IntentionalWalkListView(View):
    model = IntentionalWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        device_id = request.POST.get("device_id")

        # If any of the field is missing, return an error
        if email is None:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if device_id is None:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        try:
            user = AppUser.objects.get(email=email, device_id=device_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        intentional_walks = IntentionalWalk.objects.filter(user=user)
        # Hacky serializer
        total_steps = 0
        intentional_walk_list = []
        for intentional_walk in intentional_walks:
            intentional_walk_list.append({
                "start": intentional_walk.start,
                "end": intentional_walk.end,
                "steps": intentional_walk.steps
            })
            total_steps+=intentional_walk.steps

        payload = {
            "intentional_walks": intentional_walk_list,
            "total_steps": total_steps
        }

        return JsonResponse(payload)


    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})