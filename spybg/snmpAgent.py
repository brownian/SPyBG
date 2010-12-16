#
#
#

#import sys

from datetime import datetime, timedelta

from pysnmp.entity.rfc3413.oneliner import cmdgen

import commonFuncs

class oid:
    def __init__(self, name, value, alias=None):
        self.name = name
        self.value = value 
        self.alias = alias

    def __repr__(self):
        return str(self.value).replace('(','').replace(')','').replace(' ','').replace(',','.')


class snmpDevice:
    def __init__(self, hostname, ip, community, version='v2c',
            port=161, timeout=1, retries=3,
            ifnameoid=oid('IfName', (1,3,6,1,2,1,31,1,1,1,1), 'name')):

        self.hostname = hostname
        self.ip = ip
        self.community = community
        self.version = version
        self.port = port
        self.timeout = timeout
        self.retries = retries
        # oid to table with ifaces names:
        self.ifnameoid = ifnameoid
        # dict with fetched iface's names:
        self.ifnamesDict = dict()
        # dir where ifaces rrd bases are (should be):
        self.hostdir = None
        self.perfbase = None
        #
        # where ifaces (index -> ifname) file is:
        self.ifacesfile = None
        #
        # snmp errors:
        self.errors = 0
        # timer for snmp bulkget:
        self.snmptime = 0.0
        #
        # oids and ports to be processed:
        self.ports = []
        self.oids = []
        # storage for SNMP results:
        self.results = []


    def cbFun(self, sendRequestHandle, errorIndication, errorStatus,
            errorIndex, varBinds, cbCtx):

        """CallBack function for SNMP transport Dispatcher.

        Checks if SNMP response gives us a valid data --
        if we still are inside wanted table, returns 1,
        and Dispatcher continues walking without our intervention.
        Returns `None' if we have got all the data already.
        """

        resdict = cbCtx[0]
        baseoid = cbCtx[1]
        ports = cbCtx[2]
        doInc = cbCtx[3]

        bolen = len(baseoid)

        if errorIndication:
            print '(errorIndication:) Host %s: %s' % (
                    self.hostname, errorIndication
                )
            self.errors += 1
            return
        if errorStatus:
            print '(errorStatus:) Host %s: %s' % (
                    self.hostname, errorStatus
                )
            self.errors += 1
            return

        if isinstance(resdict, dict):
            for row in varBinds:
                for oid, val in row:
                    # if we are inside needed table:
                    if oid[:bolen] == baseoid[:bolen]:
                        # we should increment index by self.indexinc
                        # if requested:
                        if not doInc:
                            index = oid[len(oid)-1]
                        else:
                            inc = doInc and self.indexinc or 0
                            index = oid[len(oid)-1] + inc

                        # "write" value into "proper cell":
                        if not ports or index in ports:
                            resdict[index] = str(val)
                    #
                    # if we gone outside needed table:
                    else:
                        # if self.hostname == 'RC_EPON':
                        #     print
                        #     print resdict
                        return # stop on end-of-table

            return 1 # continue walking

        else:
            raise ValueError


    def asynCommandGenerator(self):
        self.asynCommandGenerator = cmdgen.AsynCommandGenerator()

        self.CommunityData = \
                cmdgen.CommunityData('testAgent', self.community)

        self.UdpTransportTarget = \
                cmdgen.UdpTransportTarget(
                        (self.ip, self.port),
                        timeout=self.timeout,
                        retries=self.retries
                    )


    def getTables(self, oids=[], results=[], ports=[], iftable=True, doInc=False):
        """Fetches wanted tables using async command generator
        and transport Dispatcher.
        
        Creates AsynCommandGenerator, adds request handles,
        and runs runDispatcher, which, for every result,
        calls cbFun (see above).
        """

        # time of start of snmp grabbing:
        starttime = datetime.today()

        oids = oids or self.oids
        results = results or self.results
        ports = iftable and (ports or self.ports) or None

        for o, r in map(None, oids, results):
            requestHandle = self.asynCommandGenerator.asyncBulkCmd(
                    self.CommunityData,
                    self.UdpTransportTarget,
                    0, 20,
                    (o.value,),
                    (self.cbFun, (r, o.value, ports, doInc))
                )

        self.asynCommandGenerator.snmpEngine.transportDispatcher.runDispatcher()

        # time of end of snmp grabbing:
        endtime = datetime.today()

        self.snmptime += commonFuncs.timedelta2secs(endtime - starttime)



    def getIfNames(self, doInc=True):
        self.getTables([self.ifnameoid], [self.ifnamesDict], doInc=doInc)


    def __str__(self):
        return """Host [%s]:
        ip = %s
        community = "%s"
        hostdir = "%s"
        ifacesfile = "%s"
        """ % (
                self.hostname,
                self.ip,
                self.community,
                self.hostdir,
                self.ifacesfile
              )




class snmpCisco(snmpDevice):
    def __init__(self, hostname, ip, community):

        snmpDevice.__init__(self, hostname, ip, community,
                version, port)

        self.ifnameoid = oid('IfName', (1,3,6,1,2,1,31,1,1,1,1), 'name')
        self.ifaliasoid = oid('IfAlias', (1,3,6,1,4,1,9,2,2,1,1,28), 'alias')



class snmpZyXEL(snmpDevice):
    def __init__(self, hostname, ip, community):

        snmpDevice.__init__(self, hostname, ip, community,
                version, port)

        self.ifnameoid = oid('IfName', (1,3,6,1,2,1,31,1,1,1,1), 'name')
        self.ifaliasoid = oid('IfAlias', (1,3,6,1,4,1,890,1,5,8,12,24,1,1,3), 'alias')


#
# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
