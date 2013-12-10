from drozer import android
from drozer.modules import common, Module
from drozer.modules.common import loader
import random
from subprocess import Popen, PIPE
import os
import time


#these are interesting
'''
android.intent.action.PHONE_STATE
android.intent.action.MCC_SET_TIME
google play (two integers, out of bounds)
com.android.providers.calendar.intent.CalendarProvider2 (com.android.phone)
android.intent.action.stk.session_end (com.android.phone)
com.google.android.apps.googlevoice.INBOX_NOTIFICATION_REGISTRATION
android.media.ACTION_SCO_AUDIO_STATE_UPDATED
com.google.android.inputmethod.dictionarypack.UPDATE_NOW
com.android.mail.action.update_notification
com.sec.spp.push.ACTION_CONNECTION_STATE_CHECK
org.dayup.gtasks.action.TASK_ALERT_SCHEDULE
com.google.android.apps.babel.CLEANUP_DB
android.net.wifi.SHOW_INFO_MESSAGE
com.sec.spp.push.receiver.PROVISIONING_ACTION
com.sec.spp.push.HEARTBEAT_ACTION
'''
#these are boring
'''
com.google.android.gms.auth.authzen.CHECK_REGISTRATION
android.intent.action.MEDIA_MOUNTED
android.intent.action.MAX_BRIGHTNESS_CHANGED
android.intent.action.GTALK_DISCONNECTED
android.intent.action.CONTENT_CHANGED
android.intent.action.SIOP_LEVEL_CHANGED
com.snapchat.android.app.NOTIFICATION
android.media.RINGER_MODE_CHANGED
android.intent.action.GTALK_CONNECTED
com.android.music.queuechanged
android.provider.Telephony.GET_SMSC
com.google.android.apps.plus.NEW_PICTURE
        '''

class IntentFuzzer (Module, common.ServiceBinding, common.Provider, common.TableFormatter):
    name="lol-name"
    description="lol-description"
    examples="lol-examples"
    author="joe"
    date="Oct 2013"
    license="none"
    path=["tools"]
    permissions=[]
    
    #Message commands (outgoing what)
    FSERV_CMD_ECHO = 0
    FSERV_CMD_FWRD = 1
    FSERV_CMD_TEST = 2
    FSERV_CMD_NULL = 3

    # mutator service forward types (outgoing arg1)
    FSERV_FWD_START_ACT = 0
    FSERV_FWD_START_ACT_FOR_RES = 1
    FSERV_FWD_SEND_BCST = 2
    FSERV_FWD_SEND_ORD_BCST = 3
    FSERV_FWD_TEST = 4

    # mutatator service fuzz types (outgoing arg2)
    FSERV_FUZZ_MUTATE = 0
    FSERV_FUZZ_MANGLE = 1
    FSERV_FUZZ_BRUTAL = 2

    # mutator service replies (incoming what)
    FSERV_REPL_TIMEOUT = 1
    FSERV_REPL_SUCCESS = 0
    FSERV_REPL_EUNIMPL = -2
    FSERV_REPL_ENOEXTRAS = -3
    FSERV_REPL_EINVPAYLOAD = -4
    FSERV_REPL_ENOTARG = -5

    # Message bundle keys
    FSERV_KEY_SEED = "mut_seed"
    FSERV_KEY_RATIO = "mut_ratio"
    FSERV_KEY_DATA = "mut_data"
    FSERV_KEY_TIMEOUT = "ipc_timout"
    FSERV_KEY_TARGPKG = "ipc_target_package"
    FSERV_KEY_TARGCMP = "ipc_target_component"

    def add_arguments(self, parser):
        #android.Intent.addArgumentsTo(parser)
        parser.add_argument("--seed", help="specify integer seed (default is rand int[1,2000] )")
        parser.add_argument("--ratio", default="0.01", help="Fuzzing ratio (default is 0.01)")
        parser.add_argument("--timeout", default="20000", help="specify a timeout in milliseconds (default is 20000)")
        parser.add_argument("--echo", action='store_true', help="send an intent echo request to the mutator (default is false)")
        parser.add_argument("--query_start", default="1", help="start index of content provider query (default is 1)")
        parser.add_argument("--query_end", default="1000", help="end index of content provider query (default is 1000)")
        parser.add_argument("--max_attempts", default="25", help="number of mutations to attempt for each action (default is 25)")
        parser.add_argument("--null", action='store_true', help="ignore other parameters, send a null intent to each broadcast component (default is false)")
        parser.add_argument("--save_payloads", action='store_true', help="queries the content provider and saves it, to be loaded later (default is false)")
        parser.add_argument("--load_payloads", action='store_true', help="instead of querying the cp, loads a fuzzing payload that was previously saved (default is false)")

    def execute(self, arguments):
            
        if arguments.null:
            self.do_null_fuzz()
        else:
            self.do_sniff_fuzz(arguments)
        return


    '''
    parse arguments to get fuzzing parameters
    '''
    def do_parse_params(self, args):
        
        mut_params = dict()
        try:
            echo = bool(args.echo)
            query_start = int(args.query_start)
            query_end = int(args.query_end)

            mut_params['mut_ratio'] = float(args.ratio)
            mut_params['mut_timeout'] = int(args.timeout)
            mut_params['mut_what'] = self.FSERV_CMD_ECHO if echo else self.FSERV_CMD_FWRD
            mut_params['mut_arg1'] = self.FSERV_FWD_SEND_BCST 
            mut_params['mut_arg2'] = self.FSERV_FUZZ_MUTATE 
            mut_params['mut_attempts'] = int(args.max_attempts)
            if args.seed:
                mut_params['mut_seed'] = int(args.seed)
        except Exception as e:
            self.stdout.write("Invalid fuzzing args Exception (%s\n):%s\n\n" % (type(e), e))
            return None
        return (mut_params, echo, query_start, query_end)

    '''
    query content provider to get seed intents 
    '''
    def do_payload_query(self, start, end):
        try:
            print 'Querying...',start, end
            rows = self.do_query_cp(start, end)
            #self.print_table(rows, show_headers=False)
            payloads = self.do_gen_payloads(rows)
        except Exception as e:
            self.stdout.write("Cursor Exception (%s\n):%s\n\n" % (type(e), e))
            return None
        return payloads

    def do_sniff_fuzz(self, arguments):
        
        (mut_params, echo, query_start, query_end) = self.do_parse_params(arguments)
        
        saveFile = './intent_payloads.txt'        

        if arguments.load_payloads:
            payloads = []
            with open(saveFile, 'r+') as fd:
                buf = ''
                for line in fd:
                    buf += line
                for row in buf.split('===='):
                    if row != '':
                        payloads.append(row.split('::::'))
        else:
            payloads = self.do_payload_query(query_start, query_end)
            if arguments.save_payloads:
                with open(saveFile, 'w+') as fd:
                    buf = ''
                    for p in payloads:
                        buf += '::::'.join(p) + '===='
                    fd.write(buf)
                return
        if not payloads:
            #something went wrong...
            self.stdout.write("Invalid payloads... try again")
            return None
        random.shuffle(payloads)

        '''
        use seed intents to fuzz & get results for logcat
        '''
        print 'fuzzing %s intents' % (str(len(payloads)))
        results = []
        Popen(['adb', 'logcat', '-c'])
        for payload in payloads:
            log_proc = Popen(['adb', 'logcat'], stdout=PIPE)
            fatal_proc = Popen(['grep','-n','-i','-A','2','exception'], stdin=log_proc.stdout, stderr=PIPE, stdout=PIPE)
            res = self.do_fuzz_intent(payload, mut_params)
            time.sleep(10)
            log_proc.kill()
            Popen(['adb', 'logcat', '-c'])
            fatal_proc.kill()
            (out, err) = fatal_proc.communicate()
            print str(out), '\n'
            results += res
            #print '\n'.join(res)
        #stdout, stderr = process.communicate()
        return

    def do_null_fuzz(self):
        mut_what = self.FSERV_CMD_NULL
        default_msg = [str(mut_what), '0', '0']
        mut_timeout = 20000
        
        arg_pkg = "com.mobilesec.mutator"
        arg_cmp = "com.mobilesec.mutator.MutatorService"
        
        binder = self.getBinding(arg_pkg, arg_cmp)
        result = binder.send_message(default_msg, mut_timeout)

        if result:
            try:
                response_message = binder.getMessage();
                response_bundle = binder.getData();
                self.stdout.write("  what: %d\n" % int(response_message.what))
                self.stdout.write("  arg1: %d\n" % int(response_message.arg1))
                self.stdout.write("  arg2: %d\n" % int(response_message.arg2))
                
                #print extras
                for n in response_bundle.split('\n'):
                    self.stdout.write("  %s\n"%n)
                return ('OK')
            except Exception as e:
                return ("Exception (%s)%s" % (type(e), e))
        else:
            return ("No reply")
    
    def do_fuzz_intent(self, payload, mut_params):
        
        results = [payload[1].split(';')[2]]
        #results = []
        cnt = 1
        if 'mut_seed' in mut_params:
            seed = mut_params['mut_seed']
        else:
            random.seed()
            seed = random.randint(1, 2000)
        print '\n' + results[0]
        #print payload[1].split(';')[2]
        arg_pkg = "com.mobilesec.mutator"
        arg_cmp = "com.mobilesec.mutator.MutatorService"
        max_attempts = mut_params['mut_attempts']

        binder = self.getBinding(arg_pkg, arg_cmp)
        while 1:
            try:
                #print '\t' + str(cnt)
                mut_seed = cnt + seed
                mut_params['mut_seed'] = mut_seed
                mut_params['extras'] = payload
                result = self.do_extras_send(binder, mut_params)
                #time.sleep(0.01)
                results.append('\t%s: %s' % (str(cnt), result))
            except Exception as e:
                results.append("Exception (%s):%s" % (type(e), e))
            finally:
                cnt += 1
                if cnt > max_attempts:
                    break
        return results

    def do_extras_send(self, binder, params):
        try:
            extras =        params['extras']
            mut_seed =      params['mut_seed']
            mut_ratio =     params['mut_ratio']
            mut_timeout =   params['mut_timeout']
            mut_what =      params['mut_what']
            mut_arg1 =      params['mut_arg1']
            mut_arg2 =      params['mut_arg2']
        except KeyError:
            return 'Broken Key, yo'
 

        #self.stdout.write("bundle_start\n")
        binder.add_extra_bundle(extras, "mut_data")
        binder.add_extra(["string","ipc_target_package","com.example.myfirstapp"])
        binder.add_extra(["string","ipc_target_component","com.example.myfirstapp.DisplayMessageActivity"])
        binder.add_extra(["float","mut_ratio", mut_ratio])
        binder.add_extra(["integer","mut_seed", mut_seed])
        default_msg = [str(mut_what), str(mut_arg1), str(mut_arg2)]
        
        result = binder.send_message(default_msg, mut_timeout)

        if result:
            try:
                response_message = binder.getMessage();
                response_bundle = binder.getData();
                #self.stdout.write("  what: %d\n" % int(response_message.what))
                #self.stdout.write("  arg1: %d\n" % int(response_message.arg1))
                #self.stdout.write("  arg2: %d\n" % int(response_message.arg2))
                
                #print extras
                '''
                for n in response_bundle.split('\n'):
                    if n.startswith('  ') and 'FUZZ_INTENT' not in n:
                        self.stdout.write("  %s\n"%n)
                '''
                return ('OK')
            except Exception as e:
                print ("Exception (%s)%s" % (type(e), e))
                return ("Exception (%s)%s" % (type(e), e))
        else:
            print ("Timeout")
            return ("Timeout")
    
    def do_query_cp(self, start, end):
        start_id = str(start)
        end_id = str(end)
        projection = None
        sort_order = None        

        self.stdout.write('querying...\n')
        cursor = self.contentResolver().query('content://com.example.contentsniffer.database/sniffertable/', projection, '(_id>?) AND (_id<?) AND (_id!=14) GROUP BY action', [start_id, end_id], sort_order)
        self.stdout.write('Getting Results\n')
        rows = self.getResultSet(cursor)
        self.stdout.write('\nGot Results\n')
        return rows
    
    def do_gen_payloads(self, rows):
        
        #TODO: These are all broadcasts that require permissions, and will cause the mutator to crash
        skip_set = set()
        skip_set.add('android.intent.action.ANY_DATA_STATE')
        skip_set.add('android.hardware.usb.action.USB_STATE')
        skip_set.add('android.net.conn.CONNECTIVITY_CHANGE')
        skip_set.add('android.net.wifi.STATE_CHANGE')
        skip_set.add('android.intent.action.NETWORK_SET_TIMEZONE')
        skip_set.add('android.intent.action.TIMEZONE_CHANGED')
        skip_set.add('android.intent.action.SERVICE_STATE')
        skip_set.add( 'android.intent.action.NEW_OUTGOING_CALL' )
        skip_set.add( 'android.intent.action.PACKAGE_REMOVED')
        skip_set.add( 'android.intent.action.PACKAGE_REPLACED')
        skip_set.add( 'android.os.UpdateLock.UPDATE_LOCK_CHANGED' )
        skip_set.add( 'android.intent.action.SIM_STATE_CHANGED')
        skip_set.add( 'android.net.conn.TETHER_STATE_CHANGED')
        skip_set.add( 'android.net.wifi.WIFI_STATE_CHANGED')
        skip_set.add( 'android.net.wifi.p2p.CONNECTION_STATE_CHANGE')
        skip_set.add( 'android.net.wifi.p2p.STATE_CHANGED')
        skip_set.add( 'android.intent.action.PACKAGE_ADDED')
        skip_set.add( 'android.bluetooth.adapter.action.STATE_CHANGED')
        skip_set.add( 'android.intent.action.RADIO_TECHNOLOGY')
        skip_set.add( 'android.bluetooth.a2dp.profile.action.CONNECTION_STATE_CHANGED')
        skip_set.add( 'android.intent.action.PACKAGE_CHANGED')
        skip_set.add( 'android.bluetooth.adapter.action.CONNECTION_STATE_CHANGED')
        skip_set.add( 'android.bluetooth.device.action.BOND_STATE_CHANGED')
        
        
        #These are boring
        skip_set.add('com.google.android.gms.auth.authzen.CHECK_REGISTRATION')
        skip_set.add('android.intent.action.MEDIA_MOUNTED')
        skip_set.add('android.intent.action.MAX_BRIGHTNESS_CHANGED')
        skip_set.add('android.intent.action.GTALK_DISCONNECTED')
        skip_set.add('android.intent.action.CONTENT_CHANGED')
        skip_set.add('android.intent.action.SIOP_LEVEL_CHANGED')
        skip_set.add('com.snapchat.android.app.NOTIFICATION')
        skip_set.add('android.media.RINGER_MODE_CHANGED')
        skip_set.add('android.intent.action.GTALK_CONNECTED')
        skip_set.add('com.android.music.queuechanged')
        skip_set.add('android.provider.Telephony.GET_SMSC')
        skip_set.add('com.google.android.apps.plus.NEW_PICTURE')
        skip_set.add('com.sec.dlc.DLC_REQUEST')
        skip_set.add('com.vp.alarmClockPlusDock.ALARM_ALERT')
        skip_set.add('com.sec.android.intent.action.DVFS_FG_PROCESS_CHANGED')
        skip_set.add('com.android.mail.ACTION_NOTIFY_DATASET_CHANGED')
        payloads = []
        intent_header = rows[0]
        for intent_row in rows[1:]:

            #skip intents with no extras!
            #also skip intents that require permissions! (see above)
            action = str(intent_row[1])
            
            if intent_row[8] == '' or action in skip_set:
                continue
            #print action
            skip_set.add(action)

            payload_i = []
            for val,head in zip(intent_row, intent_header):
                #format service is expecting: 'type;key;value'
                payload_i.append('string;{};{}'.format(str(head), str(val)))
            payloads.append(payload_i)
        return payloads
