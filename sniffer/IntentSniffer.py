from drozer.modules import Module,common

class createSniffer(Module, common.PackageManager, common.Assets):
	name=""
	description=""
	examples=""
	author=""
	date=""
	license=""
	path=[]
	
	def execute(self, arguments):
		global outputfile 
		outputfile = open("/home/parallels/Desktop/intentFilters.txt","w")
		self.stdout.write("Hello from Drozer\n")	
		for package in self.packageManager().getPackages():
			packageNameString = package.applicationInfo.packageName
			self.stdout.write("Package: %s\n" % package.applicationInfo.packageName)
			self.parse(self.getAndroidManifest(packageNameString))
		outputfile.close()
	def parse(self, manifest):
		manifestSplit = manifest.split("\n")
		startWriting = 0
		for line in manifestSplit:
			if(line == "<intent-filter>"):
				startWriting = 1
				outputfile.write(line + "\n")
			elif(line == "</intent-filter>"):
				startWriting = 0
				outputfile.write(line + "\n")
			elif(startWriting == 1):
				outputfile.write(line + "\n")
			