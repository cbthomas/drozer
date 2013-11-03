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
		outputfile = open("/home/josh-cmu/mobile-sec/drozer/sniffer/intentFilters.txt","w")
		self.stdout.write("Hello from Drozer\n")	
		for package in self.packageManager().getPackages():
			packageNameString = package.applicationInfo.packageName
			self.stdout.write("Package: %s\n" % package.applicationInfo.packageName)
			
			if(package.applicationInfo.packageName != "com.android.musicfx"):
				self.parse(self.getAndroidManifest(packageNameString))
		outputfile.close()
		
	def parse(self, manifest):
		manifestSplit = manifest.split("\n")
		open_count=0
		close_count=0
		startWriting = 0
		
		for line in manifestSplit:
			
			if(line == "<intent-filter>"):
				startWriting = 1
				open_count=open_count + 1
				outputfile.write(line + "\n")
				
			elif(line == "</intent-filter>"):
				
				if(close_count == open_count -1):
					startWriting = 0
					close_count=close_count+1
					outputfile.write(line + "\n")
				
			elif(startWriting == 1):
				line_split = line.split(" ")
				
				for word in line_split:
					
					if (("name=" in word) or ("mimeType=" in word) or ("pathPrefix=" in word) or ("scheme=" in word) or ("host=" in word) or ("path=" in word) or ("pathPattern" in word) or ("priority=" in word) or ("value=" in word)):
						outputfile.write("android:" + word + " ")
						
					else:
						outputfile.write(word + " ")
						
				outputfile.write("\n")
					
					
