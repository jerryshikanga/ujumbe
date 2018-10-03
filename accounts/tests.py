from django.test import TestCase
import africastalking, json


# Create your tests here.
class SMSTests(TestCase):
    def setUp(self):
        username = "Innovest"
        api_key = "9880bb949b67e24c1113dfccbfe19dad7ddf5666d5f85b23f867935266c327bf"
        africastalking.initialize(username, api_key)

    def test_somtel_message_delivery(self):
        sms = africastalking.SMS
        response = sms.send("Hello there, Jerry sent this", ["+252621113022", ])
        print(response)
        """
         {
            'SMSMessageData': 
                {
                    'Message': 'Sent to 1/1 Total Cost: KES 2.0156', 
                    'Recipients': 
                        [ 
                            {
                                'statusCode': 101,
                                'number': '+252628465424', 
                                'cost': 'USD 0.0200', 
                                'status': 'Success',
                                'messageId':
                                'ATXid_1ff1fd8603dd257b309deb96d4853b8c'
                            }
                        ]
                }
        }
        """
        response = json.loads(response.replace("'", '"'))
        status_code = response["SMSMessageData"]["Recipients"][0]["statusCode"]
        self.assertEquals(status_code, 101)
