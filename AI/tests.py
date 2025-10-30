from django.test import TestCase

# Create your tests here.

class SimpleTestCase(TestCase):
	def test_example(self):
		self.assertEqual(1 + 1, 2)
