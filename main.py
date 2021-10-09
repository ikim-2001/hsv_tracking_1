import json
import requests
import socket
import uuid
from threading import Thread
import time
from tangicraft_hsv import *

not_stopped = True
our_json = {}
our_uuid = ""

def get_uuid(mc_username):
    request = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{mc_username}')
    response = json.loads(request.content.decode())
    our_uuid = str(uuid.UUID(response["id"]))
    print(our_uuid)
    return our_uuid

def run(ip):
    our_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1.0)
    try:
        our_socket.connect((ip, 5003))
    except (socket.timeout, socket.gaierror, TimeoutError, ConnectionRefusedError):
        print("timed out. start client and retry")
        return

    while not_stopped:
        if our_uuid != "":
            command = {}
            command['client_name'] = our_uuid
            command['command'] = 'tbuild'
            if our_json:
                command['block_map'] = our_json
                our_socket.send((json.dumps(command) + "\n").encode())
                print(command)
        time.sleep(1)

    our_socket.close()


if __name__ == "__main__":
    global camera_index

    name = input('Please enter minecraft username: ')
    ip = input('Please enter ip address: ')
    our_uuid = get_uuid(name)

    thread1 = Thread(target=complete_hsv())
    thread1.start()

    thread = Thread(target=run, args=[ip])
    thread.start()

    try:
        while True:
            # run all of our hsv contouring opencv magic
            our_json = permanent_jsons # whatever we calculated in our current frame
            time.sleep(1)
    except KeyboardInterrupt:
        print("We were interrupted!")

    not_stopped = False

