#!/usr/bin/python
#
#

import os
# import sys

import re

import ConfigParser

from sdtg import commonFuncs, snmpAgent

#
# ifHCInMulticastPkts:  1.3.6.1.2.1.31.1.1.1.8
# ifHCOutMulticastPkts: 1.3.6.1.2.1.31.1.1.1.12
# 
# ifInDiscards:  1.3.6.1.2.1.2.2.1.13
# ifOutDiscards: 1.3.6.1.2.1.2.2.1.19
#
# ifInErrors:  1.3.6.1.2.1.2.2.1.14
# ifOutErrors: 1.3.6.1.2.1.2.2.1.20
#

oids = [
    snmpAgent.oid(
            'IfInOctets',
            (1,3,6,1,2,1,2,2,1,10),
            'in_bytes'),
    snmpAgent.oid(
            'IfOutOctets',
            (1,3,6,1,2,1,2,2,1,16),
            'out_bytes'),
    snmpAgent.oid(
            'ifInUcastPkts',
            (1,3,6,1,2,1,2,2,1,11),
            'in_upkts'),
    snmpAgent.oid(
            'ifOutUcastPkts',
            (1,3,6,1,2,1,2,2,1,17),
            'out_upkts'),
    snmpAgent.oid(
            'ifInNUcastPkts',
            (1,3,6,1,2,1,2,2,1,12),
            'in_nupkts'),
    snmpAgent.oid(
            'ifOutNUcastPkts',
            (1,3,6,1,2,1,2,2,1,18),
            'out_nupkts'),
]

HCoids = [
    snmpAgent.oid(
            'IfHCInOctets',
            (1,3,6,1,2,1,31,1,1,1,6),
            'in_bytes'),
    snmpAgent.oid(
            'IfHCOutOctets',
            (1,3,6,1,2,1,31,1,1,1,10),
            'out_bytes'),
    snmpAgent.oid(
            'ifHCInUcastPkts',
            (1,3,6,1,2,1,31,1,1,1,7),
            'in_upkts'),
    snmpAgent.oid(
            'ifHCOutUcastPkts',
            (1,3,6,1,2,1,31,1,1,1,11),
            'out_upkts'),
    snmpAgent.oid(
            'ifHCInBroadcastPkts',
            (1,3,6,1,2,1,31,1,1,1,9),
            'in_bpkts'),
    snmpAgent.oid(
            'ifHCOutBroadcastPkts',
            (1,3,6,1,2,1,31,1,1,1,13),
            'out_bpkts'),
    snmpAgent.oid(
           'ifHCInMulticastPkts',
           (1,3,6,1,2,1,31,1,1,1,8),
           'in_mpkts'),
    snmpAgent.oid(
           'ifHCOutMulticastPkts',
           (1,3,6,1,2,1,31,1,1,1,12),
           'out_mpkts'),
]

ifnameoids = {
    '1.3.6.1.2.1.31.1.1.1.1':
        snmpAgent.oid('IfName', (1,3,6,1,2,1,31,1,1,1,1), 'name'),
    '1.3.6.1.2.1.2.2.1.2':
        snmpAgent.oid('IfDescr', (1,3,6,1,2,1,2,2,1,2), 'descr'),
    '1.3.6.1.2.1.31.1.1.1.18':
        snmpAgent.oid('IfAlias', (1,3,6,1,2,1,31,1,1,1,18), 'alias'),
}


#
#D-Link:
#    Dlink DES-3026 Fast Ethernet Switch
#    DES-3226S Fast-Ethernet Switch
#
#ZyXEL:
#    GS-4012F
#    ES-3124
#


def getAliasOid(host):
    vendId = {
        'Cisco':        ( 'cisco',   (1,3,6,1,2,1,31,1,1,1,18) ),
        #
        'DES-3026':     ( 'dlink',   (1,3,6,1,2,1,31,1,1,1,18) ),
        'DES-3226S':    ( 'dlink',   (1,3,6,1,2,1,31,1,1,1,18) ),
        'Dlink':        ( 'dlink',   (1,3,6,1,2,1,31,1,1,1,18) ),
        #
        'ES-2108-G':    ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,19,19,1,1,3) ),
        'ES-3124':      ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,12,24,1,1,3) ),
        'ES-3124-4F':   ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,26,24,1,1,3) ),
        'ES-3124F':     ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,31,24,1,1,3) ),
        'GS-4012F':     ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,20,23,1,1,3) ),
        'XGS-4528F':    ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,46,23,1,1,3) ),
        'XGS-4728F':    ( 'zyxel',   (1,3,6,1,4,1,890,1,5,8,46,23,1,1,3) ),
        'ZyXEL':        ( 'zyxel',   (1,3,6,1,2,1,17,7,1,4,3,1,1) ),
        #
        'ePON':         ( 'utstar',  (1,3,6,1,2,1,2,2,1,2) ),
        #
        'ExtremeXOS':   ( 'extreme', (1,3,6,1,2,1,2,2,1,2) ),
        #
        'ZXR10':        ( 'zte', (1,3,6,1,2,1,2,2,1,2) ),
        #
        'ROS':          ( 'rc',  (1,3,6,1,2,1,2,2,1,2) ),
    }
    #
    # try to read System from device and decide:
    # oid = snmpAgent.oid('foo', (1,3,6,1,2,1,1,1), 'foo')
    oid = snmpAgent.oid('foo', (1,3,6,1,2,1,1,1), 'foo')
    result = dict()

    host.getTables(
            oids=[oid], results=[result],
            iftable=False   # that's not an ifaces table.
        )
    if host.errors != 0:
        return None

    # "guess" vendor:
    #for id in vendId.keys():
    for id, vend in vendId.items():
        # print result
        if re.compile(id).search(str(result[0])):
            return (
                    vend[0],
                    snmpAgent.oid('IfAlias', vend[1], 'alias')
                   )

    return None


class configWorker:
    def __init__(self, configfile):
        self.hosts = []
        self.configfile = configfile
        self.rrdhostdir = None
        self.perfbase = None
        self.maxthreads = 1
        #
        self.configRead()

    def configRead(self):
        # main config:
        self.config = ConfigParser.ConfigParser()
        # self.config.read(self.configfile)
        fp = open(self.configfile)
        self.config.readfp(fp)
        fp.close()
        #
        if self.config.has_option('global', 'maxthreads'):
            self.maxthreads = int(self.config.get('global', 'maxthreads'))

        #
        # default for ports:
        if self.config.has_option('hosts', 'ports'):
            ports = self.config.get('hosts', 'ports')
            if ports == 'any':
                ports = None
        else:
            ports = None

        #
        # hostdir (where rrd bases should be):
        self.rrdhostdir = self.config.get('rrd', 'dir')
        self.perfbase = self.config.get('rrd', 'perfbase')
        self.ifacesfile = self.config.get('rrd', 'ifaces')

        #
        # common snmp parameters:
        snmp_timeout = 1
        snmp_retries = 3
        if self.config.has_option('hosts', 'version'):
            snmp_version = self.config.get('hosts', 'version')
        else:
            snmp_version = '2c'
        #
        if self.config.has_section('snmp'):
            if self.config.has_option('snmp', 'timeout'):
                snmp_timeout = int(self.config.get('snmp', 'timeout'))
            if self.config.has_option('snmp', 'retries'):
                snmp_retries = int(self.config.get('snmp', 'retries'))
        #
        # config for hosts (in a separate file):
        self.hostsfile = self.config.get('hosts', 'hostsfile')
        self.hostsconfig = ConfigParser.ConfigParser()
        self.hostsconfig.read(self.hostsfile)

        hostnames = self.hostsconfig.sections()
        #
        for host in hostnames:
            #
            ip = self.hostsconfig.get(host, 'ip')
            community = self.hostsconfig.get(host, 'community')
            #
            h = snmpAgent.snmpDevice(host, ip, community)
            #
            # tmout and retries:
            snmp_to = snmp_timeout
            snmp_rt = snmp_retries
            snmp_ve = snmp_version
            #
            # timeout:
            if self.hostsconfig.has_option(host, 'timeout'):
                snmp_to = int(self.hostsconfig.get(host, 'timeout'))
            # set to host:
            if snmp_to:
                h.timeout = snmp_to
            #
            # retries:
            if self.hostsconfig.has_option(host, 'retries'):
                snmp_rt = int(self.hostsconfig.get(host, 'retries'))
            # set to host:
            if snmp_rt:
                h.retries = snmp_rt
            #
            # version:
            if self.hostsconfig.has_option(host, 'version'):
                snmp_ve = self.hostsconfig.get(host, 'version')
            # set to host:
            if snmp_ve:
                h.version = snmp_ve
            #
            # ports -- if any:
            if self.hostsconfig.has_option(host, 'ports'):
                p = self.hostsconfig.get(host, 'ports')
            else:
                p = ports
            h.ports = self.parseNumbers(p)

            #
            # ifnameoid:
            if self.hostsconfig.has_option(host, 'ifnameoid'):
                ifnameoidname = self.hostsconfig.get(host, 'ifnameoid')
                h.ifnameoid = ifnameoids[ifnameoidname]
            #
            # ifaliasoid:
            if self.hostsconfig.has_option(host, 'ifaliasoid'):
                ifaliasoidname = self.hostsconfig.get(host, 'ifaliasoid')
                h.ifaliasoid = snmpAgent.oid(
                                'IfAlias',
                                tuple(
                                    [ int(s) for s in ifaliasoidname.split('.') ]
                                ),
                                'alias')
            else:
                h.ifaliasoid = None
            #
            # rrd hostdir:
            h.hostdir = commonFuncs.cleanHostdirName(
                        '%s/%s' % (self.rrdhostdir, h.hostname)
                    )
            #
            # ifaces (index -> ifname) file:
            h.ifacesfile = self.ifacesfile
            #
            # open ini with ifnames:
            ifnamesConfig = ConfigParser.ConfigParser()
            ifnamesConfig.read('%s/%s' % (h.hostdir, h.ifacesfile))
            #
            # fill ifnamesDict:
            if ifnamesConfig.has_section('ifnames'):
                h.ifnamesDict = dict(
                        [ (int(x),y) for (x,y) in ifnamesConfig.items('ifnames') ]
                    )
            else:
                print "Error: %s/%s has no section `ifnames'" % (h.hostdir, h.ifacesfile)

            #
            #--------------------------------------------
            #
            # oids to get -- high res. (HC) by default:
            if self.hostsconfig.has_option(host, 'hc'):
                if self.hostsconfig.get(host, 'hc') in ('off', '0'):
                    h.hc = False
                    h.oids = oids
                else:
                    h.oids = HCoids
                    h.hc = True
            else:
                h.oids = HCoids
                h.hc = True

            h.results = []
            for o in h.oids:
                h.results.append(dict())
                
            h.perfbase = self.perfbase
            #--------------------------------------------

            # create cmdgen.AsynCommandGenerator() for this host:
            h.asynCommandGenerator()

            #
            ## append to a list of hosts:
            #--------------------------------------------
            self.hosts.append(h)
            #--------------------------------------------



    def configWrite(self, filename):
        raise NotImplementedError


    def parseNumbers(self, str):
        list = []
        if str:
            csv = str.split(',')
            for tok in csv:
                dsv = tok.split('-')
                if len(dsv) == 2:
                    for i in range(int(dsv[0]), int(dsv[1]) + 1):
                        list.append(i)
                elif len(dsv) == 1:
                    list.append(int(tok))
                else:
                    raise RuntimeError
            list.sort()
            return list
        else:
            return None


    def printHosts(self):
        for h in self.hosts:
            print h.hostname
            print '\t', h.ports or '( any )'
        


if __name__ == '__main__':
    cw = configWorker ( 'config.ini' )

    cw.printHosts ()

#
#
# vim: expandtab ts=4:
######################
