from channels.generic.websocket import WebsocketConsumer
from api.functions import (
    check_print_queue,
    check_transactions
)
import json


class ApiConsumer(WebsocketConsumer):
    tasks = {}

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        self.tasks[self.channel_name].revoke(terminate=True)
        try:
            self.tasks.pop(self.channel_name)
        except KeyError:
            pass

    def chat_message(self, text_data):
        self.send(text_data=json.dumps(text_data))
        self.tasks.pop(self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)

        if data['action'] == 'check_print_queue':
            task = check_print_queue.delay(self.channel_name, data['last_id'])
            self.tasks[self.channel_name] = task
        elif data['action'] == 'check_transactions':
            task = check_transactions.delay(self.channel_name, data['last_id'])
            self.tasks[self.channel_name] = task
