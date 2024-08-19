from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from home.models import Contest
from home.views.apiv2.schemas.contest import ContestSchema, ErrorSchema

router = Router()


@router.get("/current", response={200: ContestSchema, 404: ErrorSchema})
@csrf_exempt
def get_curent_contest(request):
    # get the current/next Contest
    contest = Contest.active()
    if contest is None:
        raise HttpError(404, "There are no contests")
    return 200, contest
