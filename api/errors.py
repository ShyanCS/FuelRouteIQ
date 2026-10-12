import logging
import uuid

from django.core.exceptions import RequestDataTooBig
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class PlanningError(APIException):
    def __init__(self, code, message, status=422, details=None):
        self.status_code = status
        self.payload = {"error": {"code": code, "message": message, "details": details or {}}}
        super().__init__(message)


def exception_handler(exc, context):
    if isinstance(exc, PlanningError):
        return Response(exc.payload, status=exc.status_code)
    if isinstance(exc, RequestDataTooBig):
        return Response(
            {
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "JSON body exceeds the 16 KB request limit.",
                    "details": {},
                }
            },
            status=400,
        )
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error": {
                "code": "INVALID_INPUT" if response.status_code == 400 else "HTTP_ERROR",
                "message": "Request could not be processed.",
                "details": response.data,
            }
        }
        return response
    request_id = str(uuid.uuid4())
    logging.getLogger(__name__).exception("Unhandled API failure [%s]", request_id)
    return Response(
        {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error prevented planning. Consult server logs using the request ID.",
                "details": {"request_id": request_id},
            }
        },
        status=500,
    )
