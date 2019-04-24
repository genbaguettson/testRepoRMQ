#!/usr/bin/env python3.6

from queue_rabbitmq import NewRabbitMQConnection

## Unlike the GO version, this driver in Python has neither interfaces nor function templates
## Read the doc for details on class templates and types

class ConnectionOptions:

	def __init__(self, durable = False, autoAcknowledge = False, clientId = "", groupId = "", refreshFrequency = 300000):
		"""
		:param bool durable: if you want the connection to survive a reboot
		:param bool autoAcknowledge: if you want the messages to be auto-acknowledged
		:param str clientId: the id of the created client

		ONLY USED BY KAFKA:
		:param groupId: the group to which the consumer will belong to
		:param int refreshFrequency: how often will the client update its informations like new topics (IN SECONDS)

		"""
		self.Durable = durable
		self.AutoAcknowledge = autoAcknowledge
		self.ClientID = clientId
		self.GroupID = groupId
		self.RefreshFrequency = refreshFrequency

	Durable: bool
	AutoAcknowledge: bool
	ClientID: str
	GroupID: str
	RefreshFrequency: int

class WriteOptions:

	def __init__(self, partition = 0):
		"""
		ONLY USED BY KAFKA:
		:param int partition: the number of the partition you want Kafka to write the message on

		"""
		self.Partition = partition
	Partition: int

class ReadOptions:
	"""
	This class is here as placeholder if you need read options with a new system

	"""
	pass

## NewConnection returns a new Connection according to the sys
## parameter (rabbitmq or kafka).
def NewConnection(sys, uri, name, o):
	"""If you add a new queue system to the driver, you should add an 'if' here

	:param str sys: the name of the queue system you're using
	:param str uri: the uri you want to connect to
	:param str name: the name of the connection you're going to create
	:param ConnectionOptions o: the connection options for the new connection

	"""
	if (sys == "rabbitmq"):
		return NewRabbitMQConnection(uri, name, o)
	elif (sys == "kafka"):
		return NewKafkaConnection(uri, name, o)
	else:
		raise ValueError("No such queue management system: " + sys)