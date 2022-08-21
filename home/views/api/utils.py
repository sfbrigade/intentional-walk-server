from typing import Any, Dict, List


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
