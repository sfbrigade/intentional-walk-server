import json
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
        # Parse the body json
        json_data = json.loads(request.body)

        # If any of the field is missing, return an error
        if 'name' not in json_data:
            return JsonResponse({"status": "error", "message": "Name missing"})
        if 'email' not in json_data:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if 'zip' not in json_data:
            return JsonResponse({"status": "error", "message": "Zip missing"})
        if 'age' not in json_data:
            return JsonResponse({"status": "error", "message": "Age missing"})
        if 'device_id' not in json_data:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        # Update if the object exists else create
        try:
            appuser = AppUser.objects.get(email=json_data['email'], device_id=json_data['device_id'])
            appuser.name = json_data['name']
            appuser.zip = json_data['zip']
            appuser.age = json_data['age']
            appuser.save()
            return JsonResponse({"status": "success", "message": "App User updated successfully"})

        except ObjectDoesNotExist:
            obj = AppUser.objects.create(name=json_data['name'],
                                 email=json_data['email'],
                                 zip=json_data['zip'],
                                 age=json_data['age'],
                                 device_id=json_data['device_id'])

            return JsonResponse({"status": "success", "message": "App User registered successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class DailyWalkView(View):
    model = DailyWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # If any of the field is missing, return an error
        if 'email' not in json_data:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if 'device_id' not in json_data:
            return JsonResponse({"status": "error", "message": "Device_id missing"})
        if 'date' not in json_data:
            return JsonResponse({"status": "error", "message": "Date missing"})
        if 'steps' not in json_data:
            return JsonResponse({"status": "error", "message": "Steps missing"})

        try:
            user = AppUser.objects.get(email=json_data['email'], device_id=json_data['device_id'])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        try:
            _ = DailyWalk.objects.get(user=user, date=json_data['date'])
            return JsonResponse({"status": "error", "message": "Steps already entered for this date"})
        except ObjectDoesNotExist:
            _ = DailyWalk.objects.create(date=json_data['date'],
                                           steps=json_data['steps'],
                                           user=user)

            return JsonResponse({"status": "success", "message": "Daily Walk recorded successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class DailyWalkListView(View):
    model = DailyWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        reverse_order = json_data['reverse_order'] if 'reverse_order' in json_data else False
        num_walks = json_data['num_walks'] if 'num_walks' in json_data else None

        # If any of the field is missing, return an error
        if 'email' not in json_data:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if 'device_id' not in json_data:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        try:
            user = AppUser.objects.get(email=json_data['email'], device_id=json_data['device_id'])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        # Order based on the parameters
        if reverse_order:
            daily_walks = DailyWalk.objects.filter(user=user).order_by("date")[:num_walks]
        else:
            daily_walks = DailyWalk.objects.filter(user=user)[:num_walks]

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
        json_data = json.loads(request.body)

        # If any of the field is missing, return an error
        if 'email' not in json_data:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if 'device_id' not in json_data:
            return JsonResponse({"status": "error", "message": "Device_id missing"})
        if 'start' not in json_data:
            return JsonResponse({"status": "error", "message": "Start timestamp missing"})
        if 'end' not in json_data:
            return JsonResponse({"status": "error", "message": "End timestamp missing"})
        if 'steps' not in json_data:
            return JsonResponse({"status": "error", "message": "Steps missing"})

        try:
            user = AppUser.objects.get(email=json_data['email'], device_id=json_data['device_id'])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        _ = IntentionalWalk.objects.create(start=json_data['start'],
                                             end=json_data['end'],
                                             steps=json_data['steps'],
                                             user=user)

        return JsonResponse({"status": "success", "message": "Intentional Walk recorded successfully"})

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name='dispatch')
class IntentionalWalkListView(View):
    model = IntentionalWalk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        reverse_order = json_data['reverse_order'] if 'reverse_order' in json_data else False
        num_walks = json_data['num_walks'] if 'num_walks' in json_data else None

        # If any of the field is missing, return an error
        if 'email' not in json_data:
            return JsonResponse({"status": "error", "message": "Email missing"})
        if 'device_id' not in json_data:
            return JsonResponse({"status": "error", "message": "Device_id missing"})

        try:
            user = AppUser.objects.get(email=json_data['email'], device_id=json_data['device_id'])
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "User/device not registered"})

        # Order based on the parameters
        if reverse_order:
            intentional_walks = IntentionalWalk.objects.filter(user=user).order_by("start")[:num_walks]
        else:
            intentional_walks = IntentionalWalk.objects.filter(user=user)[:num_walks]

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