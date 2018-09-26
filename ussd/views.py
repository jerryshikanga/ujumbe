from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseBadRequest
from .models import UssdSession


# Create your views here.
class USSDView(View):
    """will take the ussd request from at and interpret accordingly"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(USSDView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """ recieve request from at and interpret it"""
        phone_number = request.POST.get("phoneNumber", None)
        text = request.POST.get("text", None)
        session_id = request.POST.get("sessionId", None)

        if not phone_number or not text or not session_id:
            return HttpResponseBadRequest("Missing input")

        if not UssdSession.objects.filter(session_id=session_id).exists():
            """First time the request is being made"""
            UssdSession.objects.create(
                phone_number=phone_number,
                session_id=session_id,
            )
        else:
            """Continuing step"""
            session = UssdSession.objects.get(session_id=session_id)
            current_step = session.current_step

        return HttpResponse(status=200)
