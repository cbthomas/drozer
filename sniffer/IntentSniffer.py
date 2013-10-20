from drozer.modules import Module,common

class createSniffer(Module, common.PackageManager):
	name=""
	description=""
	examples=""
	author=""
	date=""
	license=""
	path=[]
	def execute(self, arguments):
		self.stdout.write("Hello from Drozer\n")
		for package in self.packageManager().getPackages():
			self.stdout.write("Package: %s\n" % package.applicationInfo.packageName)
