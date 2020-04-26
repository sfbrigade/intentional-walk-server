import datetime
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View, generic
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Dict, List, Any

from .models import AppUser, Contest, DailyWalk, IntentionalWalk


def validate_request_json(json_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
    """Generic function to check the request json payload for required fields
    and create an error response if missing

    Parameters
    ----------
    json_data
        Input request json converted to a python dict
    required_fields
        Fields required in the input json

    Returns
    -------
        Dictionary with a boolean indicating if the input json is validated and
        an optional error message

    """
    # Create a default success message
    response = {"status": "success"}
    for required_field in required_fields:
        if required_field not in json_data:
            # Set the error fields
            response["status"] = "error"
            response["message"] = f"Required input '{required_field}' missing in the request"
            # Fail on the first missing key
            break

    return response


@method_decorator(csrf_exempt, name="dispatch")
class AppUserCreateView(View):
    """View to create and update an AppUser
    """
    model = AppUser
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Parse the body json
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["name", "email", "zip", "age", "account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Update if the object exists else create
        # EMAIL CANNOT BE UPDATED!
        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
            # If it is an email update
            if appuser.email != json_data["email"]:
                return JsonResponse({"status": "error", "message": "Email cannot be updated. Contact admin"})
            appuser.name = json_data["name"]
            appuser.zip = json_data["zip"]
            appuser.age = json_data["age"]
            appuser.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "App User updated successfully",
                    "payload": {
                        "name": appuser.name,
                        "email": appuser.email,
                        "zip": appuser.zip,
                        "age": appuser.age,
                        "account_id": appuser.account_id,
                    },
                }
            )

        # This implies that it is a new user
        except ObjectDoesNotExist:
            obj = AppUser.objects.create(
                name=json_data["name"],
                email=json_data["email"],
                zip=json_data["zip"],
                age=json_data["age"],
                account_id=json_data["account_id"],
            )

            # To validate, retrieve the object back and send the details in the response
            try:
                appuser = AppUser.objects.get(email=json_data["email"], account_id=json_data["account_id"])
            except ObjectDoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "App User failed to save successfully. Please retry",}
                )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "App User registered successfully",
                    "payload": {
                        "name": appuser.name,
                        "email": appuser.email,
                        "zip": appuser.zip,
                        "age": appuser.age,
                        "account_id": appuser.account_id,
                    },
                }
            )

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class ContestCurrentView(View):
    """View to retrieve current Contest
    """
    model = Contest
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        today = datetime.date.today()
        # get the current/next Contest
        contest = Contest.objects.filter(end__gte=today).order_by("start").first()
        if contest is None:
            # get the last contest
            contest = Contest.objects.order_by("-end").first()
        if contest is None:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"There are no contests",
                }
            )
        return JsonResponse(
            {
                "status": "success",
                "payload": {
                    "contest_id": contest.contest_id,
                    "start": contest.start,
                    "end": contest.end,
                }
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkCreateView(View):
    """View to create and update a Daily Walk
    """
    model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id", "daily_walks"],)
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the app user if the account exists
        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        json_response = {
            "status": "success", "message": f"Dailywalks recorded successfully",
            "payload": {
                "account_id": appuser.account_id,
                "daily_walks": [],
            }
        }
        for daily_walk_data in json_data["daily_walks"]:
            # Validate data
            json_status = validate_request_json(daily_walk_data, required_fields=["date", "steps", "distance"],)
            if "status" in json_status and json_status["status"] == "error":
                return JsonResponse(json_status)

            # Check if there is already an entry for this date. If there is, update the entry
            try:
                daily_walk = DailyWalk.objects.get(appuser=appuser, date=daily_walk_data["date"])
                daily_walk.steps = daily_walk_data["steps"]
                daily_walk.distance = daily_walk_data["distance"]
                daily_walk.save()
                json_response["payload"]["daily_walks"].append({
                    "date": daily_walk.date,
                    "steps": daily_walk.steps,
                    "distance": daily_walk.distance
                })
            except ObjectDoesNotExist:
                daily_walk = DailyWalk.objects.create(
                    date=daily_walk_data["date"], steps=daily_walk_data["steps"], distance=daily_walk_data["distance"], appuser=appuser
                )
                json_response["payload"]["daily_walks"].append({
                    "date": daily_walk.date,
                    "steps": daily_walk.steps,
                    "distance": daily_walk.distance
                })
        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class DailyWalkListView(View):
    """View to retrieve Daily Walks
    """
    model = DailyWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        # Get walks from all the accounts tied to the email
        # NOTE: This is very hacky and cannot distinguish between legit and fake users
        # Someone can simply install the app on a new device and use a known email id
        # and have the metrics simply aggregated.
        # For the simple use case, this is likely not an issue and would need to be
        # handled manually if needed
        all_users = AppUser.objects.filter(email=appuser.email)
        daily_walks = []
        for user_obj in all_users:
            daily_walks += DailyWalk.objects.filter(appuser=user_obj)
        # Hacky code to group by date and keep the latest entry
        daily_walk_dict = {}
        for daily_walk in daily_walks:
            # If date already is there, keep only the latest entry
            if daily_walk.date in daily_walk_dict:
                if daily_walk.updated > daily_walk_dict[daily_walk.date].updated:
                    daily_walk_dict[daily_walk.date] = daily_walk
            else:
                daily_walk_dict[daily_walk.date] = daily_walk

        # Update dailywalks
        daily_walks = list(daily_walk_dict.values())

        # Hacky serializer
        total_steps = 0
        total_distance = 0
        daily_walk_list = []
        for daily_walk in daily_walks:
            daily_walk_list.append({"date": daily_walk.date, "steps": daily_walk.steps, "distance": daily_walk.distance})
            total_steps += daily_walk.steps
            total_distance += daily_walk.distance

        # Sort the list based on the date
        daily_walk_list = sorted(daily_walk_list, key=lambda x: x['date'], reverse=True)
        # Create the payload with meta information and send it back
        payload = {"daily_walks": daily_walk_list, "total_steps": total_steps, "total_distance": total_distance, "status": "success"}
        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkView(View):
    """View to create Intentional Walks
    """
    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(
            json_data, required_fields=["account_id", "intentional_walks"],
        )
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        # Get the app user if the account exists
        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        json_response = {
            "status": "success", "message": "Intentional Walks recorded successfully",
            "payload": {
                "account_id": appuser.account_id,
                "intentional_walks": []
            }
        }
        for intentional_walk_data in json_data["intentional_walks"]:
            json_status = validate_request_json(
                intentional_walk_data, required_fields=["event_id", "start", "end", "steps", "pause_time", "distance"],
            )
            if "status" in json_status and json_status["status"] == "error":
                return JsonResponse(json_status)

            try:
                intentional_walk = IntentionalWalk.objects.create(
                    event_id=intentional_walk_data["event_id"],
                    start=intentional_walk_data["start"],
                    end=intentional_walk_data["end"],
                    steps=intentional_walk_data["steps"],
                    distance=intentional_walk_data["distance"],
                    pause_time=intentional_walk_data["pause_time"],
                    appuser=appuser
                )
                json_response["payload"]["intentional_walks"].append({
                    "event_id": intentional_walk.event_id,
                    "start": intentional_walk.start,
                    "end": intentional_walk.end,
                    "steps": intentional_walk.steps,
                    "distance": intentional_walk.distance,
                    "pause_time": intentional_walk.pause_time,
                })
            except:
                # IntentionalWalk records are immutable- so ignore any errors
                # that might occur if the record already exists, etc...
                pass

        return JsonResponse(json_response)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


@method_decorator(csrf_exempt, name="dispatch")
class IntentionalWalkListView(View):
    """View to retrieve Intentional Walks
    """
    model = IntentionalWalk
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)

        # Validate json. If any field is missing, send back the response message
        json_status = validate_request_json(json_data, required_fields=["account_id"])
        if "status" in json_status and json_status["status"] == "error":
            return JsonResponse(json_status)

        try:
            appuser = AppUser.objects.get(account_id=json_data["account_id"])
        except ObjectDoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"User does not exist for account - {json_data['account_id']}. Please register first!",
                }
            )

        # Get walks from all the accounts tied to the email
        # NOTE: Same issue as with daily walks
        all_users = AppUser.objects.filter(email=appuser.email)
        intentional_walks = []
        for user_obj in all_users:
            intentional_walks += IntentionalWalk.objects.filter(appuser=user_obj)

        # Hacky serializer
        total_steps = 0
        total_walk_time = 0
        total_pause_time = 0
        total_distance = 0
        intentional_walk_list = []
        for intentional_walk in intentional_walks:
            intentional_walk_list.append(
                {"event_id": intentional_walk.event_id, "start": intentional_walk.start, "end": intentional_walk.end, "steps": intentional_walk.steps,
                 "distance": intentional_walk.distance, "walk_time": intentional_walk.walk_time, "pause_time": intentional_walk.pause_time}
            )
            total_steps += intentional_walk.steps
            total_walk_time += intentional_walk.walk_time
            total_distance += intentional_walk.distance
            total_pause_time += intentional_walk.pause_time
        intentional_walk_list = sorted(intentional_walk_list, key=lambda x: x['start'], reverse=True)
        payload = {
            "intentional_walks": intentional_walk_list,
            "total_steps": total_steps,
            "total_walk_time": total_walk_time,
            "total_pause_time": total_pause_time,
            "total_distance": total_distance,
            "status": "success"
        }

        return JsonResponse(payload)

    def http_method_not_allowed(self, request):
        return JsonResponse({"status": "error", "message": "Method not allowed!"})


class HomeView(generic.ListView):
    template_name = "home/home.html"
    model = AppUser

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['appuser_list'] = AppUser.objects.all()
        all_emails = set(AppUser.objects.values_list('email', flat=True))
        context['total_users'] = len(all_emails)
        # TODO: This is very inefficient. This should be a member function of the model
        all_daily_walks = []
        for email in all_emails:
            users_accounts = AppUser.objects.filter(email=email)
            user_daily_walks = []
            for users_account in users_accounts:
                user_daily_walks += DailyWalk.objects.filter(appuser=users_account)
            # Hacky code to group by date and keep the latest entry
            user_daily_walk_dict = {}
            for user_daily_walk in user_daily_walks:
                # If date already is there, keep only the latest entry
                if user_daily_walk.date in user_daily_walk_dict:
                    if user_daily_walk.updated > user_daily_walk_dict[user_daily_walk.date].updated:
                        user_daily_walk_dict[user_daily_walk.date] = user_daily_walk
                else:
                    user_daily_walk_dict[user_daily_walk.date] = user_daily_walk

            # Update dailywalks
            all_daily_walks += list(user_daily_walk_dict.values())

        total_steps = 0
        total_distance = 0
        for daily_walk in all_daily_walks:
            total_steps += daily_walk.steps
            total_distance += daily_walk.distance

        context['total_steps'] = total_steps
        context['total_distance'] = total_distance
        context['total_daily_walks'] = len(all_daily_walks)
        context['total_intentional_walks'] = len(IntentionalWalk.objects.all())

        return context


class UserView(generic.DetailView):
    template_name = "home/user.html"
    model = AppUser

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        print(self)
        users_accounts = AppUser.objects.filter(email=self.object.email)
        # TODO: This is very inefficient. This should be a member function of the model
        daily_walks = []
        for users_account in users_accounts:
            daily_walks += DailyWalk.objects.filter(appuser=users_account)
        # Hacky code to group by date and keep the latest entry
        daily_walk_dict = {}
        for daily_walk in daily_walks:
            # If date already is there, keep only the latest entry
            if daily_walk.date in daily_walk_dict:
                if daily_walk.updated > daily_walk_dict[daily_walk.date].updated:
                    daily_walk_dict[daily_walk.date] = daily_walk
            else:
                daily_walk_dict[daily_walk.date] = daily_walk

        # Update dailywalks
        daily_walks = list(daily_walk_dict.values())

        total_steps = 0
        total_distance = 0
        for daily_walk in daily_walks:
            total_steps += daily_walk.steps
            total_distance += daily_walk.distance

        context['total_steps'] = total_steps
        context['total_distance'] = total_distance
        context['daily_walk_list'] = sorted(daily_walks, key=lambda x: x.date, reverse=True)
        context['total_daily_walks'] = len(daily_walks)

        # Get all the intentional walks
        all_users = AppUser.objects.filter(email=self.object.email)
        intentional_walks = []
        for user_obj in all_users:
            intentional_walks += IntentionalWalk.objects.filter(appuser=user_obj)
        context['intentional_walk_list'] = sorted(intentional_walks, key=lambda x: x.start, reverse=True)
        context['total_intentional_walks'] = len(intentional_walks)
        return context
