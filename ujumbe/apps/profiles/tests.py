from django.test import TestCase
from django.test.utils import override_settings
from ujumbe.apps.profiles.tasks import send_sms


# Create your tests here.
class SMSTests(TestCase):
    def test_somtel_message_delivery(self):
        # disclaimer : this will send an actual message if settings are true
        send_sms.delay(phonenumber=int("+252621113022"), text="Hello there, Jerry sent this")

    @override_settings(EMAIL_HOST="smtp-mail.outlook.com")
    @override_settings(EMAIL_PORT="587")
    @override_settings(EMAIL_HOST_USER="Jerry.Lumbasi@Chebupharma.com")
    @override_settings(EMAIL_HOST_PASSWORD="Navalayo.1970")
    @override_settings(EMAIL_USE_TLS=True)
    @override_settings(EMAIL_USE_SSL=False)
    def test_send_mail(self):
        from django.core.mail import send_mail
        send_mail('Test Subject', 'Test body of the message. This was send via django SMTP', 'Jerry.Lumbasi@Chebupharma.com',
                  ['michael.wangia@gmail.com', 'elisha.wangia@chebupharma.com'])
