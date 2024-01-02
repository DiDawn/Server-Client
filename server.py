import socket
from threading import Thread
from logger import Log
import json
import numpy as np
from PIL import Image


class Server:
    def __init__(self, port, save_log=True):
        """
        :type port: int
        :type save_log: bool
        You must call listen() to start listening for connections.
        To send a message to a client, you need to send the message type first, then the message.
        """
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((socket.gethostbyname(socket.gethostname()), port))
        self.save_log = save_log
        self.log = Log(self.save_log)

    def handle_client(self, conn, addr):
        self.log.append(f'[NEW CONNECTION] {addr} connected.')
        connected = True
        while connected:
            msg_type, msg = self.receive_msg(conn)

            connected = self.handle_msg(conn, addr, msg_type, msg)

        conn.close()

    def handle_msg(self, conn, addr, msg_type, msg):
        """
        :type conn: socket.socket
        :type addr: tuple
        :type msg_type: str
        :type msg: bytes
        :return: False if the connection should be closed, True otherwise
        """

        if msg_type == 'txt':
            msg = msg.decode('utf-8')
            if msg == 'close':
                self.log.append(f'[DISCONNECTED] {addr} disconnected.')
                return False
            else:
                self.log.append(f'[MESSAGE] {addr} sent: {msg}')

        elif msg_type == 'json':
            msg = json.loads(msg.decode('utf-8'))
            self.log.append(f'[MESSAGE] {addr} sent: {msg}')

        elif msg_type == 'image_as_array':
            self.log.append(f'[MESSAGE] {addr} sent an image')
            self.handle_image_as_array(conn, msg)

        return True

    def handle_image_as_array(self, conn, array_bytes: bytes):
        array = np.frombuffer(array_bytes, dtype=np.uint8)
        shape = self.receive(conn).decode('utf-8')
        shape = tuple(map(int, shape[1:-1].split(', ')))
        array = array.reshape(shape)
        Image.fromarray(array).show()

    @staticmethod
    def receive(conn) -> bytes:
        msg_length = conn.recv(64).decode('utf-8')
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length)
            return msg

    @staticmethod
    def _send(conn, message: bytes):
        msg_length = len(message)
        send_length = str(msg_length).encode('utf-8')
        send_length += b' ' * (64 - len(send_length))
        conn.send(send_length)
        conn.send(message)

    @staticmethod
    def send_type(conn, msg_type):
        Server._send(conn, msg_type.encode('utf-8'))

    @staticmethod
    def send_txt(conn, msg: str):
        Server.send_type(conn, 'txt')
        message = msg.encode('utf-8')
        Server._send(conn, message)

    @staticmethod
    def send_json(conn, msg: dict):
        Server.send_type(conn, 'json')
        message = json.dumps(msg).encode('utf-8')
        Server._send(conn, message)

    def receive_msg(self, conn) -> (str, bytes):
        """
        :param conn:
        :return: msg type and msg
        """
        msg_type = self.receive(conn).decode('utf-8')
        msg = self.receive(conn)

        return msg_type, msg

    def listen(self):
        self.socket.listen()
        while True:
            conn, addr = self.socket.accept()
            Thread(target=self.handle_client, args=(conn, addr)).start()


if __name__ == '__main__':
    server = Server(5050)
    server.listen()
