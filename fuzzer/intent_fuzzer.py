from drozer.modules import Module

class IntentFuzzer (Module):
	name=""
	description=""
	examples=""
	author=""
	date=""
	license=""
	path=[]
	def execute(self, arguments):
		self.stdout.write("Hello from Drozer")
