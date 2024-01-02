import socket
import json
from threading import Thread


class Client:
    def __init__(self, port, ip=None):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ip is not None:
            self.socket.connect((ip, port))
        else:
            self.socket.connect((socket.gethostbyname(socket.gethostname()), port))

        self.connected = True

        self.receive_loop_thread = Thread(target=self.receive_loop)
        self.receive_loop_thread.start()

    def _send(self, message: bytes):
        msg_length = len(message)
        send_length = str(msg_length).encode('utf-8')
        send_length += b' ' * (64 - len(send_length))
        self.socket.send(send_length)
        self.socket.send(message)

    def send_txt(self, msg: str):
        self.send_type('txt')
        message = msg.encode('utf-8')
        self._send(message)

    def send_json(self, msg: dict):
        self.send_type('json')
        message = json.dumps(msg).encode('utf-8')
        self._send(message)

    def send_image_as_array(self, array):
        self.send_type('image_as_array')
        array_bytes = array.tobytes()
        self._send(array_bytes)
        shape = str(array.shape).encode('utf-8')
        self._send(shape)

    def send_type(self, msg_type):
        self._send(msg_type.encode('utf-8'))

    def _receive(self):
        msg_length = self.socket.recv(64).decode('utf-8')
        if msg_length:
            msg_length = int(msg_length)
            msg = self.socket.recv(msg_length).decode('utf-8')
            return msg

    def receive_msg(self):
        """
        :return: the type of msg and the msg
        """
        msg_type = self._receive()
        msg = self._receive()
        return msg_type, msg

    def receive_loop(self):
        while self.connected:
            msg_type, msg = self.receive_msg()

            self.connected = self.handle_msg(msg_type, msg)

        self.socket.close()

    @staticmethod
    def handle_msg(msg_type, msg) -> bool:
        if msg_type == 'txt':
            msg = msg.decode('utf-8')
            if msg == 'close':
                return False
            else:
                print(f'[MESSAGE] {msg}')
        elif msg_type == 'json':
            msg = json.loads(msg.decode('utf-8'))
            print(f'[MESSAGE] {msg}')


if __name__ == '__main__':
    client = Client(5050, '190')
    client.send_json({'name': 'John', 'age': 30})
    client.send_txt('close')
