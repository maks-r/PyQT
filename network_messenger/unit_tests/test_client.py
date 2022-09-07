import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from client.variables_client import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, TYPE, STATUS, ACTION, PRESENCE
from client.client_msg import response_server, presence


class TestClientClass(unittest.TestCase):
    def test_presence(self):
        test = presence()
        test[TIME] = 1.1
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, TYPE: STATUS, USER: {ACCOUNT_NAME: 'Maks', STATUS: 'Привет'}})

    def test_answer_200(self):
        self.assertEqual(response_server({RESPONSE: 200}), '200 : Соединение установлено')

    def test_answer_400(self):
        self.assertEqual(response_server({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError, response_server, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()

