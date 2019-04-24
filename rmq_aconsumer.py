#!/usr/bin/env python3.6

import time
import pika
from colors import colors

from queue_rabbitmq import RabbitMQMessage

class Consumer(object):
	def __init__(self, o, message_queue):
		self.Connection = None
		self.Channel = None
		self.closing = False
		self.consumer_tag = None

		self.url = None
		self.o = o
		self.message_queue = message_queue

		self.exchange_name = None
		self.queue = None
		self.on_message_callback = None

	def connect(self, url):
		self.Connection = pika.BlockingConnection(pika.URLParameters(url))
		self.url = url
		self.Channel = self.Connection.channel()

	def setup_exchange(self, exname):
		self.Channel.exchange_declare(exname, "topic", False, True)
		self.exchange_name = exname

	def setup_queue(self, qname):
		res = self.Channel.queue_declare(queue = qname)
		self.queue = res.method.queue

	def bind_topic(self, topic):
		self.Channel.queue_bind(self.queue, self.exchange_name, topic)

	def setup_consume(self):
		self.consumer_tag = self.Channel.basic_consume(self.queue, self.on_message)

	def on_message(self, unused_channel, basic_deliver, properties, body):
		message = RabbitMQMessage(self, basic_deliver, properties, body.decode())
		self.on_message_callback(message, self.message_queue)

	def run(self):
		self.Channel.start_consuming()

	def stop(self):
		self.Channel.basic_cancel(self.consumer_tag)
		if (self.Connection.is_open):
			self.Connection.close()