#!/usr/bin/env python3.6

import pika
import time
from queue import Queue
from colors import colors

import rmq_aconsumer as aconsumer
from queue_classes import NewConnection, ConnectionOptions, ReadOptions, WriteOptions

def TestRabbitMQ():
	options = ConnectionOptions(durable = True, autoAcknowledge = False)
	uri = "amqp://guest:guest@localhost:5672/"
	print(colors.HEADER + colors.BOLD + "\n=== RabbitMQ Testing: BASIC TESTS ===\n" + colors.ENDC)
	testSimpleSendReceive("rabbitmq", uri, options)
	print(colors.HEADER + colors.BOLD + "\n=== RabbitMQ Testing: THE FORBIDDEN TESTS: BACKGROUND READING ===\n" + colors.ENDC)
	testBackgroundReading("rabbitmq", uri, options)
	print(colors.OKBLUE + colors.BOLD + "\n=== RabbitMQ Testing: ALL TESTS HAVE PASSED ===" + colors.ENDC)

def handlerBackground(message, queue):
	print(colors.OKBLUE + "Received: " + message.Body() + colors.ENDC)
	queue.put(message)

def testBackgroundReading(system: str, uri: str, o):
	o.ClientID = "test_read_background_" + str(int(time.time()))
	try:
		c = NewConnection(
			system,
			uri,
			"tmp_test_" + system,
			o
		)
	except:
		raise ValueError("You most likely need to run " + system + " (docker-compose up)")
	print(colors.OKGREEN + "\n-> CONNECTION ESTABLISHED <-\n" + colors.ENDC)

	topic_seed = str(int(time.time()))
	msgs = ["first", "second", "third"]
	topic = "background." + topic_seed
	ch = Queue()

	## subscribe to topic
	try:
		c.Subscribe(topic)
	except:
		c.Close()
		raise ValueError("Could not subscribe to topic")
	print("-> SUBBED TO TOPIC <-")
	
	## start reading
	try:
		c.ReadBackground(handlerBackground, ch, o)
	except:
		c.Close()
		raise ValueError("Could not start background reader")
	print("-> STARTED BACKGROUND READER <-")

	## write message
	try:
		c.Write(topic, msgs[0], WriteOptions())
	except:
		c.Close()
		raise ValueError("Could not write message")
	print("-> WROTE FIRST MESSAGE <-")

	time.sleep(1)

	## check that
	msg = ch.get()
	if msg.Body() != msgs[0]:
		c.Close()
		print(colors.FAIL + "Expected \"" + msgs[0] + "\" but got \"" + msg.Body() + "\"" + colors.ENDC)
		raise Exception("Message differs from message expected")
	print(colors.OKGREEN + colors.BOLD + "-> MESSAGE MATCHED EXPECTATIONS <-\n" + colors.ENDC)

	## stop reading
	try:
		c.StopReader()
	except:
		c.Close()
		raise ValueError("Could not stop background reader")
	print("-> STOPPED BACKGROUND READER <-")

	## write second message
	try:
		c.Write(topic, msgs[1], WriteOptions())
	except:
		c.Close()
		raise ValueError("Could not write second message")
	print("-> WROTE SECOND MESSAGE <-")

	msg = None
	## select timeout and message channel
	try:
		msg = ch.get(timeout = 3)
	except:
		print(colors.OKGREEN + colors.BOLD + "-> BACKGROUND READER WAS STOPPED <-" + colors.ENDC)
	if msg:
		c.Close()
		print(colors.FAIL + "Got \"" + msg.Body() + "\"" + colors.ENDC)
		raise ValueError("Second message received correctly but did not stop reading")

	c.Close()

def testSimpleSendReceive(system, uri, o):
	o.ClientID = "test_send_receive_" + str(int(time.time()))
	c = NewConnection(
		system,
		uri,
		"tmp_test_" + system,
		o
	)
	print(colors.OKGREEN + "-> CONNECTION ESTABLISHED <-\n" + colors.ENDC)

	topic_seed = str(int(time.time()))

	topic = "aled." + topic_seed
	msg = "oskour"

	c.Subscribe(topic)
	c.Write(topic, msg, WriteOptions())
	message = c.Read(ReadOptions())
	if message.Body() == msg:
		print(colors.OKGREEN + colors.BOLD + "-> MESSAGE MATCHED EXPECTATIONS <-\n" + colors.ENDC)
	else:
		exit(84)

	msg = "wassup"
	message.Reply(msg)
	message.Close()
	reply = c.ReplyChan()
	readReply = reply.get()
	if (readReply.Body() == msg):
		print(colors.OKGREEN + colors.BOLD + "-> READ REPLY MATCHES EXPECTATIONS <-" + colors.ENDC)
	else:
		exit(84)

	#readReply.Close()

	c.Close()

TestRabbitMQ()