from unittest import TestCase

from openscoring import EvaluationRequest, Openscoring
from pandas import DataFrame

import os
import pandas
import tempfile

class TestOpenscoring(TestCase):

	def testReadme(self):
		openscoring = Openscoring()

		pmml = os.path.join(os.path.dirname(__file__), "resources", "DecisionTreeIris.pmml")

		modelResponse = openscoring.deploy("Iris", pmml)
		self.assertEqual("Iris", modelResponse.id)

		arguments = {
			"Sepal_Length" : 5.1,
			"Sepal_Width" : 3.5,
			"Petal_Length" : 1.4,
			"Petal_Width" : 0.2
		}
		result = openscoring.evaluate("Iris", arguments)
		self.assertEqual({"Species" : "setosa", "Probability_setosa" : 1.0, "Probability_versicolor" : 0.0, "Probability_virginica" : 0.0, "Node_Id" : "2"}, result)
		evaluationRequest = EvaluationRequest("record-001", arguments)
		evaluationResponse = openscoring.evaluate("Iris", evaluationRequest)
		self.assertEqual(evaluationRequest.id, evaluationResponse.id)
		self.assertEqual("setosa", evaluationResponse.result["Species"])

		inCsv = os.path.join(os.path.dirname(__file__), "resources", "input.csv")
		outCsv = os.path.join(tempfile.gettempdir(), "output.csv")

		self.assertFalse(os.path.isfile(outCsv))
		openscoring.evaluateCsv("Iris", inCsv, outCsv)
		self.assertTrue(os.path.isfile(outCsv) and os.path.getsize(outCsv) > 10)

		os.remove(outCsv)

		arguments = pandas.read_csv(inCsv, sep = ",")
		result = openscoring.evaluateDataFrame("Iris", arguments)
		self.assertEqual(arguments["Id"].tolist(), result["Id"].tolist())
		self.assertEqual(["setosa", "versicolor", "virginica"], result["Species"].tolist())

		openscoring.undeploy("Iris")

		with self.assertRaises(Exception) as context:
			openscoring.evaluateDataFrame("Iris", arguments)
		self.assertEqual("Model \"Iris\" not found", str(context.exception))

class TestDictMerge(TestCase):

	def testMissingUserDict(self):
		self.assertEqual({}, Openscoring._merge(None))
		self.assertEqual({"A" : 1}, Openscoring._merge(None, A = 1))
		self.assertEqual({"A" : {"one" : 1}}, Openscoring._merge(None, A = {"one" : 1}))

	def testMergeValue(self):
		self.assertEqual({"A" : 1, "B" : 2, "C" : 3}, Openscoring._merge({"A" : 1}, B = 2, C = 3))

	def testMergeValueEqual(self):
		self.assertEqual({"A" : 1}, Openscoring._merge({"A" : 1}, A = 1))

	def testMergeValueConflict(self):
		with self.assertRaises(Exception):
			Openscoring._merge({"A" : 1}, A = "1")

	def testMergeDict(self):
		self.assertEqual({"A" : {"one" : 1, "two" : 2, "three" : 3}}, Openscoring._merge({"A" : {"one" : 1}}, A = {"two" : 2, "three" : 3}))

	def testMergeDictOverride(self):
		self.assertEqual({"A" : {"one" : 1}}, Openscoring._merge({"A" : {"one" : 1}}))
		self.assertEqual({"A" : {"one" : "1"}}, Openscoring._merge({"A" : {"one" : 1}}, A = {"one" : "1"}))
