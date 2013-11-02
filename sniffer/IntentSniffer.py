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
		outputfile = open("intentFilters.txt","w")
		self.stdout.write("Hello from Drozer\n")	
		for package in self.packageManager().getPackages():
			packageNameString = package.applicationInfo.packageName
			self.stdout.write("Package: %s\n" % package.applicationInfo.packageName)
			self.parse(self.getAndroidManifest(packageNameString))
		outputfile.close()
	def parse(self, manifest):
		manifestSplit = manifest.split("\n")
		startWriting = 0
		duplicate = 0
		for line in manifestSplit:
			if(line == "<intent-filter>"):
				startWriting = 1
				duplicate = 0
				outputfile.write(line + "\n")
			elif(line == "</intent-filter>" and duplicate == 0):
				startWriting = 0
				duplicate = 1
				outputfile.write(line + "\n")
			elif(startWriting == 1):
				line_split = line.split(" ")
				for word in line_split:
					if (("name=" in word) or ("mimeType=" in word) or ("pathPrefix=" in word) or ("scheme=" in word) or ("host=" in word) or ("path=" in word) or ("pathPattern" in word) or ("priority=" in word) or ("value=" in word)):
						outputfile.write("android:" + word + " ")
					else:
						outputfile.write(word + " ")
				outputfile.write("\n")
					
					
