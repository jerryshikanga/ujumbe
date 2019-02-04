import datetime
import json
import logging
import re

from django.http.response import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from rest_framework import status
from rest_framework.views import View as DRFView

from ujumbe.apps.africastalking.models import IncomingMessage, UssdSession, OutgoingMessages, Message
from ujumbe.apps.africastalking.serializers import TelerivetSerializer, AfricastalkingIncomingMessageSerializer, AfricastalkingOutgoingMessageSerializer
from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.profiles.tasks import create_customer_account, create_user_forecast_subscription, \
    end_user_subscription, send_user_balance_notification, send_user_account_charges, \
    set_user_location
from ujumbe.apps.weather.models import Location, ForecastWeather
from ujumbe.apps.weather.tasks import send_user_current_location_weather, send_user_forecast_weather_location
from ujumbe.apps.weather.utils import get_ussd_formatted_weather_forecast_periods, get_location_not_found_response

logger = logging.getLogger(__name__)


# Create your views here.
class ATIncomingMessageCallbackView(DRFView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ATIncomingMessageCallbackView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = AfricastalkingIncomingMessageSerializer(data=request.POST)
        if serializer.is_valid():
            message = serializer.save()
            fields = ["id", "provider_id", "text"]
            return JsonResponse(model_to_dict(message, fields=fields), status=status.HTTP_201_CREATED)
        else:
            logger.error(str(serializer.errors))
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST, )


class AtOutgoingSMSCallback(DRFView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AtOutgoingSMSCallback, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = AfricastalkingOutgoingMessageSerializer(data=self.request.POST)
        if serializer.is_valid():
            message = serializer.save()
            return JsonResponse(model_to_dict(message, fields=['id', 'delivery_status',]), status=status.HTTP_201_CREATED)
        else:
            logger.error(str(serializer.errors))
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST, )


class AtUssdcallbackView(DRFView):
    request_successful_response = "Your response has been received and will be processed. You will be notified via " \
                                  "SMS.\n "
    invalid_data_response = "You have entered invalid data. Please try again.\n"

    def is_valid_str_response(self, data=None):
        if data is None:
            return False
        if not isinstance(data, str):
            return False
        return True

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AtUssdcallbackView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            # Reads the variables sent via POST
            request_data = json.loads(request.body.decode('utf-8'))
            session_id = request_data.get("sessionId", None)
            service_code = request_data.get("serviceCode", None)
            phonenumber = request_data.get("phoneNumber", None)
            text = request_data.get("text", "")
            text = str(text).strip()
            parts = text.split("*")

            if session_id is None or phonenumber is None:
                return HttpResponse(status=400)

            ussd_session = UssdSession.objects.filter(session_id=session_id).first()
            if ussd_session is None:
                ussd_session = UssdSession.objects.create(
                    session_id=session_id,
                    service_code=service_code,
                    phonenumber=phonenumber,
                    text=text
                )
            else:
                ussd_session.service_code = service_code
                ussd_session.text = text
                ussd_session.save()

            response_text = ""
            if not Profile.objects.filter(telephone=phonenumber).exists():
                if text == "":
                    response_text = "CON You don't have an account. Choose an option : \n"
                    response_text += "0. Register \n"
                    response_text += "99. Exit\n"
                elif text == "0":
                    response_text += "CON Enter your first name:"
                elif re.match("0\*\w+", text) and len(parts) == 2:
                    first_name = parts[1] if self.is_valid_str_response(parts[1]) else None
                    response_text = "CON Enter last name " if first_name is not None else "END " + self.invalid_data_response

                elif re.match("0\*\w+\*\w+", text) and len(parts) == 3:
                    last_name = parts[2] if parts[2] is not None else None
                    first_name = parts[1] if parts[1] is not None else None
                    response_text = "END " + self.request_successful_response if self.is_valid_str_response(
                        last_name) else "END " + self.invalid_data_response
                    if not Profile.objects.filter(telephone=phonenumber).exists():
                        create_customer_account.delay(first_name=first_name, last_name=last_name,
                                                      phonenumber=phonenumber)
                    else:
                        response_text = "END You already have an account."
            else:
                profile = Profile.objects.filter(telephone=phonenumber).first()
                # no text entered by user
                if text == "":
                    response_text = "CON Choose Operation\n"
                    response_text += "1. Current Weather Data\n"
                    response_text += "2. Forecast Weather Data\n"
                    response_text += "3. Subscriptions\n"
                    response_text += "4. Manage Account\n"

                # Customer has an accoiunt so end
                elif text == "0" or re.match("0\*\w+", text):
                    response_text = "END You already have an account."

                elif text == "1":
                    response_text = "CON : Choose location\n"
                    response_text += "1. Enter location\n"
                    if profile.location is not None:
                        response_text += "2. Default location ({})\n".format(profile.location.name)

                elif text == "1*2":
                    response_text = "END Your current location weather will be sent to you shortly via SMS."
                    send_user_current_location_weather.delay(phonenumber=phonenumber)

                elif text == "1*1":
                    response_text = "CON Enter location name."

                elif re.match("1\*1\*\w+", text) is not None and len(text.split("*")) == 3:
                    parts = text.split("*")
                    location = Location.try_resolve_location_by_name(name=parts[2], phonenumber=phonenumber)
                    if location is None:
                        response_text = "END {}".format(get_location_not_found_response(parts[2]))
                    else:
                        response_text = "END Your current location weather will be sent to you shortly via SMS."
                        send_user_current_location_weather.delay(phonenumber=phonenumber, location_id=location.id)

                elif text == "2":
                    response_text = "CON : Choose location\n"
                    response_text += "1. Enter location name\n"
                    if profile.location is not None:
                        response_text += "2. Default location ({})\n".format(profile.location.name)

                elif text == "2*1":
                    response_text = "CON Enter location name."

                elif re.match(r"2\*1\*\w+", text) is not None and len(text.split("*")) == 3:
                    parts = text.split("*")
                    location = Location.try_resolve_location_by_name(name=parts[2], phonenumber=phonenumber)
                    if location is None:
                        response_text = "END {}".format(get_location_not_found_response(parts[2]))
                    else:
                        response_text = "CON Choose period."
                        response_text += get_ussd_formatted_weather_forecast_periods()

                elif text == "2*2":
                    response_text = "CON Choose period."
                    response_text += get_ussd_formatted_weather_forecast_periods()

                elif re.match(r"2\*1\*\w+\*\d", text) is not None or re.match(r"2\*2\*\d", text) is not None:
                    parts = text.split("*")
                    if re.match(r"2\*1\*\w+\*\d", text) is not None:
                        parts = text.split("*")
                        location = Location.try_resolve_location_by_name(name=parts[2], phonenumber=phonenumber)
                        period = parts[3]
                    elif re.match(r'2\*2\*d', text) is not None:
                        location = profile.location
                        period = parts[2]
                    else:
                        location = None
                        period = 0
                    period = ForecastWeather.PeriodOptions.choices[int(period) - 1]
                    send_user_forecast_weather_location.delay(location_id=location.id, phonenumber=phonenumber,
                                                              period=period)
                    if location is not None and period != 0:
                        response_text = "END Your request has been received for processing"
                    else:
                        response_text = "END Invalid data. Please try again"

                # Implement Subscriptions
                elif text == "3":
                    response_text = "CON"
                    response_text += "1. View subscriptions \n"
                    response_text += "2. Add subscriptions \n"
                    response_text += "3. Unsubscribe \n"
                elif text == "3*1":
                    response_text = "END Your request has been received successfully."
                    send_user_subscriptions.delay(phonenumber=phonenumber)
                elif text == "3*2":
                    response_text = "CON Choose Frequency"
                    response_text += get_ussd_formatted_weather_forecast_periods()
                elif re.match("3\*2\*\d", text):
                    response_text = "CON Enter Location"
                elif re.match("3\*2\*\d\*\w+", text):
                    parts = text.split("*")
                    location = Location.try_resolve_location_by_name(name=parts[3], phonenumber=phonenumber)
                    if location is not None:
                        response_text = "END Your request has been received and will be processed."
                        create_user_forecast_subscription.delay(phonenumber=phonenumber, location_id=location.id,
                                                                frequency=parts[2])
                    else:
                        response_text = "END {}".format(get_location_not_found_response(parts[3]))
                elif text == "3*3":
                    response_text = "CON Choose Option to Unsubscribe"
                    subscriptions = Subscription.objects.for_phonenumber(phonenumber)
                    for s in subscriptions:
                        response_text += "{}. {}\n".format(s.id, str(s))
                elif re.match("3\*3\*\d", text):
                    parts = text.split("*")
                    end_user_subscription.delay(phonenumber=phonenumber, subscription_id=(int(parts[2])))
                    response_text = "END Request received successfully."

                # Implement Accounts
                elif text == "4":
                    response_text = "CON Welcome to your account. Choose an option.\n"
                    response_text += "1. View Balance\n"
                    response_text += "2. View Charges\n"
                    response_text += "3. Update location\n"

                elif text == "4*1":
                    response_text = "END Request received successfully."
                    send_user_balance_notification.delay(phonenumber=phonenumber)
                elif text == "4*2":
                    response_text = "END Request received successfully."
                    send_user_account_charges.delay(phonenumber=phonenumber)
                elif text == "4*3":
                    response_text = "CON Enter location name."
                elif re.match("4\*2\*\w+", text):
                    parts = text.split("*")
                    location = Location.try_resolve_location_by_name(name=parts[2], phonenumber=phonenumber)
                    if location is None:
                        response_text = "END {}".format(get_location_not_found_response(parts[2]))
                    else:
                        response_text = "END Request received successfully."
                        set_user_location.delay(phonenumber=phonenumber, location_id=location.id)
                elif text == "99":
                    response_text = "END Thank you and goodbye our valued patner."
                else:
                    response_text = "END " + self.invalid_data_response
            ussd_session.update_last_response(response_text)
            return HttpResponse(status=200, content_type="text/plain", content=response_text)
        except Exception as e:
            logging.error(e)
            return HttpResponse(status=400)


class TelerivetWebhookView(DRFView):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(TelerivetWebhookView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = TelerivetSerializer(data=request.POST)
        if serializer.is_valid():
            message = serializer.save()
            return JsonResponse(model_to_dict(message, fields=['id', 'delivery_status',]), status=status.HTTP_200_OK)
        else:
            logger.error(str(serializer.errors))
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST, )
