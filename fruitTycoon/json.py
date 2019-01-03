import json
import logging

log = logging.getLogger('root')

class Json:

	def __init__(self, json_file, load=True):
		self.file = json_file
		if load:
			self.data = self.parse()
		else:
			self.data = {}

	def parse(self):
		"""Load and parse the JSON file"""
		with open(self.file, encoding='utf-8') as f:
			try:
				data = json.load(f)
			except Exception:
				log.error("JSON: error loading {} as JSON".format(self.file))
				data = {}
			f.close()
		return data

	def get(self, item, fallback=None, detect_blanks=False):
		"""Get an item from a JSON file"""
		try:
			data = self.data[item]
		except KeyError:
			log.warning("JSON: could not get {} data from {}".format(item, self.file))
			data = fallback
		
		if detect_blanks:
			if data == "":
				data = fallback
		return data

	def dump(self, data):
		"""Save data to JSON file"""
		with open(self.file, 'w', encoding='utf-8') as f:
			try:
				json.dump(data, f)
			except Exception as e:
				log.warning(e)
				f.close()
				return None
			f.close()

		return True