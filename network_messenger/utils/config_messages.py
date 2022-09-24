
import json
import sys
sys.path.append('../')
from utils.decorators import log
from utils.settings import MAX_PACKAGE_LENGTH, ENCODING


@log
def get_msg(client):
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_msg(sock, message):
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
