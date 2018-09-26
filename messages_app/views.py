from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Message
from django.http import HttpResponse


# Create your views here.
class AfricastalkingMessageCallback(View):
    """Will recive message from at and process it"""

    @method_decorator(csrf_exempt())
    def dispatch(self, request, *args, **kwargs):
        return super(AfricastalkingMessageCallback, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request_data = request.post
        from_telephone = request_data.get("from", "")
        to_telephone = request_data.get("to", "")
        text = request_data.get("text", "")
        date = request_data.get("date", "")
        africastalking_id = request_data.get("id", "")
        link_id = request_data.get("linkId", "")

        # save message
        Message.objects.create(
            from_telephone=from_telephone,
            to_telephone=to_telephone,
            text=text,
            africastalking_id=africastalking_id,
            link_id=link_id
        )

        # get which action message is and process it
        # actions
        """
        LOGIN
        REGISTER
        DATA
        -WEATHER
            RAINFALL
            HUMIDITY
            TEMPERATURE
            SUNSHINE
            PRECIPITATION
        -MARKET
            PRODUCT SPECIFIC
        **SCOPE
            HISTORICAL
            PREDICTIVE
        **DURATION
            HOUR
            DAY
            WEEK
            MONTH
            YEAR



        check message contents
        it has to contain keyword followed by input data e.g LOGIN password
        """

        return HttpResponse(status=200)