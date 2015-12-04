#!/usr/bin/env python

from json import JSONDecoder, JSONEncoder

import json
import requests
import shutil

__copyright__ = "Copyright (c) 2015 Villu Ruusmann"
__license__ = "GNU Affero General Public License (AGPL) version 3.0"

class SimpleRequest(object):
	pass

class EvaluationRequest(SimpleRequest):

	def __init__(self, id = None, arguments = {}):
		self.id = id
		self.arguments = arguments

class SimpleResponse(object):

	def __init__(self, message = None):
		self.message = message

	def ensureSuccess(self):
		if(hasattr(self, "message") and self.message is not None):
			raise Exception(self.message)
		return self

class EvaluationResponse(SimpleResponse):

	def __init__(self, message = None, id = None, result = {}):
		SimpleResponse.__init__(self, message)
		self.id = id
		self.result = result

class ModelResponse(SimpleResponse):

	def __init__(self, message = None, id = None, miningFunction = None, summary = None, properties = {}, schema = {}):
		SimpleResponse.__init__(self, message)
		self.id = id
		self.miningFunction = miningFunction
		self.summary = summary
		self.properties = properties
		self.schema = schema

class RequestEncoder(JSONEncoder):

	def default(self, request):
		if(isinstance(request, SimpleRequest)):
			return request.__dict__
		else:
			return JSONEncoder.default(self, request)

class Openscoring:

	def __init__(self, baseUrl = "http://localhost:8080/openscoring"):
		self.baseUrl = baseUrl

	@staticmethod
	def _merge(userDict, **systemDict):
		if(userDict is None):
			return systemDict
		for key in systemDict:
			if(key in userDict):
				if(isinstance(userDict[key], dict) and isinstance(systemDict[key], dict)):
					userDict[key].update(systemDict[key])
				elif(userDict[key] == systemDict[key]):
					pass
				else:
					raise Exception()
			else:
				userDict[key] = systemDict[key]
		return userDict

	def deploy(self, id, pmml, **kwargs):
		stream = open(pmml, "rb")
		try:
			kwargs = Openscoring._merge(kwargs, data = stream, json = None, headers = {"content-type" : "application/xml"})
			#print(kwargs)
			response = requests.put(self.baseUrl + "/model/" + id, **kwargs)
			modelResponse = ModelResponse(**json.loads(response.content))
			return modelResponse.ensureSuccess()
		finally:
			stream.close()

	def evaluate(self, id, payload = {}, **kwargs):
		if(isinstance(payload, EvaluationRequest)):
			evaluationRequest = payload
		else:
			evaluationRequest = EvaluationRequest(None, payload)
		kwargs = Openscoring._merge(kwargs, data = json.dumps(evaluationRequest, cls = RequestEncoder), json = None, headers = {"content-type" : "application/json"})
		#print(kwargs)
		response = requests.post(self.baseUrl + "/model/" + id, **kwargs)
		evaluationResponse = EvaluationResponse(**json.loads(response.content))
		evaluationResponse.ensureSuccess()
		if(isinstance(payload, EvaluationRequest)):
			return evaluationResponse
		else:
			return evaluationResponse.result

	def evaluateCsv(self, id, inCsv, outCsv, **kwargs):
		inStream = open(inCsv, "r")
		try:
			kwargs = Openscoring._merge(kwargs, data = inStream, json = None, headers = {"content-type" : "text/plain"}, stream = True)
			#print(kwargs)
			response = requests.post(self.baseUrl + "/model/" + id + "/csv", **kwargs)
			try:
				if("content-encoding" in response.headers):
					response.raw.decode_content = True

				if(("content-type" in response.headers) and (response.headers["content-type"] == "application/json")):
					simpleResponse = SimpleResponse(**json.loads(response.content))
					return simpleResponse.ensureSuccess()

				outStream = open(outCsv, "w")
				try:
					shutil.copyfileobj(response.raw, outStream, 1024)
				finally:
					outStream.close()
			finally:
				response.close()
		finally:
			inStream.close()

	def undeploy(self, id, **kwargs):
		response = requests.delete(self.baseUrl + "/model/" + id, **kwargs)
		simpleResponse = SimpleResponse(**json.loads(response.content))
		return simpleResponse.ensureSuccess()