from drozer.modules import Module,common
from drozer.modules.common import PackageManager

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
		installedPackageManager = PackageManager.packageManager(self)
		installedPackages = installedPackageManager.getPackages(0)
		for i in installedPackages:
			self.stdout.write(i)
