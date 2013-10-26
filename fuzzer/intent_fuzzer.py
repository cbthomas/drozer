from drozer import android
from drozer.modules import common, Module

class IntentFuzzer (Module, common.ServiceBinding):
	name="lol"
	description="lol"
	examples="lol"
	author="joe "
	date=" Oct 2013"
	license=" none"
	path=["tools"]
	permissions=["com.mwr.example.sieve.READ_KEYS"]
    
	def add_arguments(self, parser):
		parser.add_argument("package", help="the package containing the target service")
		parser.add_argument("component", help="the fully-qualified service name to bind to")
		parser.add_argument("--msg", nargs=3, metavar=("what", "arg1", "arg2"), help="specify the what, arg1 and arg2 values to use when obtaining the message")
		parser.add_argument("--extra", action="append", nargs=3, metavar=("type","key","value"), help="add an extra to the message's data bundle")
		parser.add_argument("--no-response", action="store_true", default=False, help="do not wait for a response from the service")
		parser.add_argument("--timeout", default="20000", help="specify a timeout in milliseconds (default is 20000)")
	
	def execute(self, arguments):
		if arguments.msg is None:
			self.stderr.write("please specify --msg as \"what arg1 arg2\"\n")
			return

		binder = self.getBinding(arguments.package, arguments.component)
		if arguments.extra is not None:
			#self.stdout.write("args Not null, yo\n")
			for extra in arguments.extra:
				binder.add_extra(extra)
				for e in extra:
					self.stdout.write('::' + e + '\n')
		#real_binder = binder.obtain_binder()
		#self.stdout.write(real_binder.printData())

		if arguments.no_response:
			binder.send_message(arguments.msg, -1)

			self.stdout.write("Sent message, did not wait for a reply from %s/%s.\n" % (arguments.package, arguments.component))
		else:
			result = binder.send_message(arguments.msg, arguments.timeout)

			if result:
				response_message = binder.getMessage();
				response_bundle = binder.getData();

				self.stdout.write("Got a reply from %s/%s:\n" % (arguments.package, arguments.component))
				self.stdout.write("  what: %d\n" % int(response_message.what))
				self.stdout.write("  arg1: %d\n" % int(response_message.arg1))
				self.stdout.write("  arg2: %d\n" % int(response_message.arg2))

				for n in response_bundle.split('\n'):
					self.stdout.write("  %s\n"%n)
			else:
				self.stdout.write("Did not receive a reply from %s/%s.\n" % (arguments.package, arguments.component))

