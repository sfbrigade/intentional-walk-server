import functools
from math import ceil
from typing import Any, Dict, List, Callable
from django.http import HttpResponse
from django.views import View


def paginate(request, results, page, per_page):
    count = results.count()
    pages_count = ceil(count / per_page)
    base_url = f"{request.scheme}://{request.get_host()}{request.path}"
    query = request.GET.copy()
    links = []
    if page < pages_count:
        query["page"] = page + 1
        links.append(f'<{base_url}?{query.urlencode()}>; rel="next"')
    if page < pages_count - 1:
        query["page"] = pages_count
        links.append(f'<{base_url}?{query.urlencode()}>; rel="last"')
    if page > 2:
        query["page"] = 1
        links.append(f'<{base_url}?{query.urlencode()}>; rel="first"')
    if page > 1:
        query["page"] = page - 1
        links.append(f'<{base_url}?{query.urlencode()}>; rel="prev"')
    return (
        results[(page - 1) * per_page : page * per_page],  # noqa: E203
        ", ".join(links),
    )


def validate_request_json(
    json_data: Dict[str, Any], required_fields: List[str]
) -> Dict[str, str]:
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
            response[
                "message"
            ] = f"Required input '{required_field}' missing in the request"
            # Fail on the first missing key
            break

    return response


def require_authn(func: Callable[[View, Any, Any], HttpResponse]):
    """Decorator for Django View methods to require authn.

    Checks if the request's user is authenticated. If not, returns a 401 HttpResponse.
    Otherwise, calls the decorated method.

    Parameters
    ----------
    func:
        The View method to decorate.

    Returns
    -------
        The decorated method.

    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponse(status=401)
        return func(self, *args, **kwargs)

    return wrapper
