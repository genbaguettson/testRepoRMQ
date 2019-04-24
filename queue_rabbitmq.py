#!/usr/bin/env python3.6

import pika
import time
from threading import Thread
from queue import Queue

import rmq_aconsumer as aconsumer

class RabbitMQConnection:

	def __init__(self, Connection = None, Channel = None, ExchangeName = None, Queue = None, ReplyQueue = None, Options = None, url = ""):
		self.Connection = Connection
		self.Channel = Channel
		self.ExchangeName = ExchangeName
		self.Queue = Queue
		self.ReplyQueue = ReplyQueue
		self.Options = Options
		self.url = url

		self.bgReplyReader = None
		self.bgReplyThread = None

		self.replyQueue = None

	def Subscribe(self, topic):
		self.Channel.queue_bind(self.Queue, self.ExchangeName, topic)

	def Unsubscribe(self, topic):
		self.Channel.queue_unbind(self.Queue, self.ExchangeName, topic)

	def Write(self, topic, message, o):
		props = pika.BasicProperties(delivery_mode = 2, reply_to = "reply-" + self.Queue, content_type = "text/plain")
		self.Channel.basic_publish(self.ExchangeName, topic, message, props)

	def Read(self, o):
		method, header, body = self.Channel.basic_get(
			queue = self.Queue,
			auto_ack = self.Options.AutoAcknowledge
		)
		message = RabbitMQMessage(self, method, header, body.decode())
		return message

	def ReadBackground(self, f, message_queue, o):
		if self.bgReader:
			return self.bgReader.message_queue

		bgReader = aconsumer.Consumer(o, message_queue)
		bgReader.on_message_callback = f
		bgReader.queue = self.Queue
		bgReader.auto_ack = self.Options.AutoAcknowledge

		bgReader.connect(self.url)
		bgReader.open_channel()
		bgReader.setup_exchange(self.ExchangeName)
		bgReader.setup_queue(self.Options.ClientID)
		for topic in self.Subscriptions:
			bgReader.bind_topic(topic)
		bgReader.setup_consume()

		t = Thread(target = bgReader.run)
		t.start()

		self.bgReader = bgReader
		self.bgThread = t

	def ReplyChan(self):
		if self.bgReplyReader:
			return self.bgReplyReader.message_queue

		replyQueue = Queue()

		bgReplyReader = aconsumer.Consumer(self.Options, replyQueue)
		bgReplyReader.on_message_callback = lambda m, q : q.put(m)

		bgReplyReader.connect(self.url)
		bgReplyReader.setup_exchange(self.ExchangeName)
		bgReplyReader.setup_queue("repq")
		bgReplyReader.bind_topic("reply-" + self.Queue)
		bgReplyReader.setup_consume()

		t = Thread(target = bgReplyReader.run)
		t.start()

		self.bgReplyReader = bgReplyReader
		self.bgReplyThread = t

		return replyQueue

	def StopReader(self):
		if self.bgReplyReader:
			self.bgReplyReader.stop()
			self.bgReplyReader = None
		if self.bgReplyThread:
			self.bgReplyThread.join()
			self.bgReplyThread = None

	def Close(self):
		self.StopReader()
		self.Channel.close()
		if self.Connection.is_open:
			self.Connection.close()

class RabbitMQMessage:

	def __init__(self, conn = None, method = None, header = None, body = None):
		self.Connection = conn
		self.DeliveryMethod = method
		self.DeliveryHeader = header
		self.DeliveryBody = body

	def Body(self):
		return self.DeliveryBody

	def Sender(self):
		return self.DeliveryHeader.reply_to

	def Reply(self, message):
		props = pika.BasicProperties(delivery_mode = 2, content_type = "text/plain")
		self.Connection.Channel.basic_publish(self.Connection.ExchangeName, self.Sender(), message, props)

	def Close(self):
		self.Connection.Channel.basic_ack(self.DeliveryMethod.delivery_tag)

def NewRabbitMQConnection(uri, name, o):
	conn = RabbitMQConnection(Options = o, url = uri)

	parameters = pika.URLParameters(uri)
	rmqConn = pika.BlockingConnection(parameters)
	conn.Connection = rmqConn

	rmqChan = rmqConn.channel()
	conn.Channel = rmqChan

	conn.ExchangeName = name
	conn.Channel.exchange_declare(conn.ExchangeName, "topic", False, True)

	result = rmqChan.queue_declare(o.ClientID)
	conn.Queue = result.method.queue

	result = rmqChan.queue_declare("repq")
	conn.ReplyQueue = result.method.queue

	conn.Channel.queue_bind(conn.ReplyQueue, conn.ExchangeName, "reply-" + conn.Queue)

	return conn
