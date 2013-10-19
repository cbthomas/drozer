from drozer.modules import Module

class createSniffer(Module):
	name=""
	description=""
	examples=""
	author=""
	date=""
	license=""
	path=[]
	def execute(self, arguments):
		self.stdout.write("Hello from Drozer")
