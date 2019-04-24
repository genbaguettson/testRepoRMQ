#!/usr/bin/env python3.6

import re

def catRegexps(regexps):
	"""Joins the given regex array into one big regex

	:param array[str] regexps: the array of regexes to concat

	"""
	tmp = []
	for regexp in regexps:
		tmp.append(toRegex(regexp))
	finalReg = "|".join(tmp)
	return finalReg

def toRegex(string):
	"""Translates the given string to a usable regex (only handles the * operator)

	:param str string: the string to translate

	"""
	res = "^" + string + "$"
	res = res.replace(".", "\.")
	res = res.replace("*", ".*")
	return res

def filterByRegex(regex, array):
	"""Deletes string in the given array if they match the given regex

	:param str regex: the regex to match the given array with
	:param array[str] array: the array to filter

	"""
	newArray = []
	for r in array:
		if not (re.search(toRegex(regex), r)):
			newArray.append(r)
	return newArray