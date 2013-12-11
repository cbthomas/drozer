from drozer.modules import Module,common

import os

class createSniffer(Module, common.PackageManager, common.Assets):
	name=""
	description=""
	examples=""
	author=""
	date=""
	license=""
	path=['cmu']
	
	def execute(self, arguments):
		global outputfile 
		os.system("echo Scanning...this can take up to a couple of minutes. Be patient!")
		os.system("mkdir /usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp")
		os.system("cp /usr/local/lib/python2.7/dist-packages/drozer/modules/tools/template/* -r /usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp/")
		outputfile = open("/usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp/AndroidManifest.xml","a")
		for package in self.packageManager().getPackages():
			packageNameString = package.applicationInfo.packageName
			#self.stdout.write(".")
			if(package.applicationInfo.packageName != "com.android.musicfx"):
				self.parse(self.getAndroidManifest(packageNameString))
		outputfile.write("</receiver> \n </application> \n </manifest>")
		outputfile.close()
		os.system("android update project --target 2 --path /usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp --name ContentSniffer")
		os.chdir("/usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp")
		os.system("ant debug install")
		os.system("rm -r /usr/local/lib/python2.7/dist-packages/drozer/modules/tools/snifferApp")
		
	def parse(self, manifest):
		manifestSplit = manifest.split("\n")
		open_count=0
		close_count=0
		startWriting = 0
		
		for line in manifestSplit:
			
			#open intent filter could contain a label which we cannot replicate
			if("<intent-filter" in line):
				startWriting = 1
				open_count=open_count + 1
				outputfile.write("<intent-filter>" + "\n")
				
			elif(line == "</intent-filter>"):
				
				if(close_count == open_count -1):
					startWriting = 0
					close_count=close_count+1
					outputfile.write(line + "\n")
				
			elif(startWriting == 1):
				line_split = line.split(" ")
				
				for word in line_split:
					
					if (("name=" in word) or ("mimeType=" in word) or ("pathPrefix=" in word) or ("scheme=" in word) or ("host=" in word) or ("path=" in word) or ("pathPattern" in word) or ("priority=" in word) or ("value=" in word) or ("port=" in word) or ("permission=" in word)):
						outputfile.write("android:" + word + " ")
						
					else:
						outputfile.write(word + " ")
						
				outputfile.write("\n")
					
					
