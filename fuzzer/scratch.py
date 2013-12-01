
    def do_default_send(self):

        random.seed()
        
        arg_pkg = "com.mobilesec.mutator"
        arg_cmp = "com.mobilesec.mutator.MutatorService"

        binder = self.getBinding(arg_pkg, arg_cmp)

        self.stdout.write("bundle_start\n")
        extras = ["string;com.example.myfirstapp.MESSAGE;AAAAAAAAAAAAAAAAAA"]
        binder.add_extra_bundle(extras, "mut_data")
        self.stdout.write("bundle_done\n")
        binder.add_extra(["string","ipc_target_package","com.example.myfirstapp"])
        binder.add_extra(["string","ipc_target_component","com.example.myfirstapp.DisplayMessageActivity"])
        binder.add_extra(["float","mut_ratio",float(0.01)])
        binder.add_extra(["integer","mut_seed",random.randint(1,1000)])
        default_msg = ["0","0","3"]
        
        result = binder.send_message(default_msg, 20000)

        if result:
            response_message = binder.getMessage();
            response_bundle = binder.getData();

            self.stdout.write("Got a reply from %s/%s:\n" % (arg_pkg, arg_cmp))
            self.stdout.write("  what: %d\n" % int(response_message.what))
            self.stdout.write("  arg1: %d\n" % int(response_message.arg1))
            self.stdout.write("  arg2: %d\n" % int(response_message.arg2))

            for n in response_bundle.split('\n'):
                self.stdout.write("  %s\n"%n)
        else:
            self.stdout.write("Did not receive a reply from %s/%s.\n" % (arg_pkg, arg_cmp))

    def do_broadcast_fuzz(self, seed, intent):
        results = []
        keepFuzzing = True
        if intent.isValid():
            while(keepFuzzing):
                # pass to mutator
                # wait for result
                # check for heartbeat
                result = send_to_mutator_proxy(intent)
                results.append(result) 
        else:
            self.stderr.write("invalid intent: one of action or component must be set")
 
    def do_activity_fuzz(self, intent):
        if len(intent.flags) == 0:
            intent.flags.append('ACTIVITY_NEW_TASK')

        if intent.isValid():
            self.getContext().startActivity(intent.buildIn(self))
        else:
            self.stderr.write("invalid intent: one of action or component must be set\n")
 
    def do_service_start_fuzz(self, intent):
        if intent.isValid():
            self.getContext().startService(intent.buildIn(self))
        else:
            self.stderr.write("invalid intent: one of action or component must be set\n")


    def do_service_bind_fuzz(self, arguments):

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

    def send_to_mutator_proxy(seed, payload_intent, timeout):
        #build new intent 
        #add payload intent as an extra
        #send to mutator proxy

        fuzz_pkg = "com.example.myfirstservice"        
        fuzz_comp = "com.example.myfirstservice"        

        binder = self.getBinding(fuzz_pkg, fuzz_comp)
        binder.add_extra(["integer", "timeout", timeout])
        binder.add_extra(["integer", "seed", seed])
        binder.add_extra(payload_intent)
        
        msg = "what arg1 arg2"
        result = None #binder.send_message(msg, timeout)

        if result:
            # fuzzer sent us a response
            response_message = binder.getMessage();
            response_bundle = binder.getData();
        
            what = int(response_message.what)
            
            if(what == SUCCESS):
                # no crash
                self.stdout.write("result=SUCCESS")
            elif(what == TIMEOUT):
                # timeout
                self.stdout.write("result=TIMEOUT")
            elif(what == ERROR):
                # something went wrong
                self.stdout.write("result=ERROR")
        else:
            # check for dc
            if binder.hadCrash():
                # fuzzer crash
                self.stdout.write("result=FUZZER_CRASH")
            else:
                # fuzzer timeout
                self.stdout.write("result=FUZZER_TIMEOUT")
