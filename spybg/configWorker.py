#!/usr/bin/python
#
#

import os
# import sys

import re

import ConfigParser

import commonFuncs, snmpAgent, oidManager

"""
ifnameoids = {
    '1.3.6.1.2.1.31.1.1.1.1':
        snmpAgent.oid('IfName', (1,3,6,1,2,1,31,1,1,1,1), 'name'),
    '1.3.6.1.2.1.2.2.1.2':
        snmpAgent.oid('IfDescr', (1,3,6,1,2,1,2,2,1,2), 'descr'),
    '1.3.6.1.2.1.31.1.1.1.18':
        snmpAgent.oid('IfAlias', (1,3,6,1,2,1,31,1,1,1,18), 'alias'),
}
"""

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
            iftable=False  # that's not an ifaces table
        )

    if host.errors != 0:
        return None

    # "guess" vendor:
    for id, vend in vendId.items():
        if re.compile(id).search(result[0]):
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

    def oidsRead(self, configfile=None):
        # TODO: check configfile.
        self.oidscfg = ConfigParser.ConfigParser()
        self.oidscfg.read(self.configfile)
        self.oidMgr = oidManager.oidManager()
        #
        # read oids subsets and sets:
        # sets[setname] -> list of oids
        subsets = dict()
        for subset , value in self.oidscfg.items('oids_subsets'):
            subsets[subset] = [ s.strip() for s in value.split(',') ]

        sets = dict()
        for set_ , value in self.oidscfg.items('oids_sets'):
            sets[set_] = []
            for s in value.split(','):
                sets[set_].extend(subsets[s.strip()])

        #
        # read config file and "fill" oidMgr with oids:
        for alias, values in self.oidscfg.items('oids'):
            alias_value = values.split()
            av_len = len(alias_value)
            if av_len == 4:
                oid_as_str, rrdDST, rrdMin, rrdMax = alias_value
            elif av_len == 3:
                oid_as_str, rrdDST, rrdMin = alias_value
                rrdMax = 4250000000
            elif av_len == 2:
                oid_as_str, rrdDST = alias_value
                rrdMin = 0
                rrdMax = 4250000000
            else:
                oid_as_str = alias_value[0]
                rrdDST = 'COUNTER'
                rrdMin = 0
                rrdMax = 4250000000
            
            for g, l in sets.items():
                if alias in l:
                    self.oidMgr.newOid(
                            alias,
                            commonFuncs.string2tuple(oid_as_str, func=int),
                            alias,
                            memberof=[g],
                            rrdDST=rrdDST,
                            rrdMin=int(rrdMin),
                            rrdMax=int(rrdMax)
                            )

        #for k, v in self.oidMgr.sets.items():
        #    print '%s -> %s' % (k, ', '.join([s.alias for s in v]))

    def configRead(self):
        # read oids:
        self.oidsRead()
        
        # main config:
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.configfile)
        #
        if self.config.has_option('global', 'maxthreads'):
            self.maxthreads = int(self.config.get('global', 'maxthreads'))

        ##
        ## default for ports:
        #if self.config.has_option('hosts', 'ports'):
        #    ports = self.config.get('hosts', 'ports')
        #    if ports == 'any':
        #        ports = None
        #else:
        #    ports = None

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
                p = None

            h.ports = self.parseNumbers(p)

            #
            # ifnameoid:
            if self.hostsconfig.has_option(host, 'ifnameoid'):
                ifnameoidname = self.hostsconfig.get(host, 'ifnameoid')
                h.ifnameoid = self.oidMgr.newOid(
                        'IfName',
                        tuple([int(s) for s in ifnameoidname.split('.')]),
                        'ifname')
            #else:
            #   # set by default to IfName -- see snmpAgent.snmpDevice.__init__()
            #   pass

            # ifaliasoid:
            if self.hostsconfig.has_option(host, 'ifaliasoid'):
                ifaliasoidname = self.hostsconfig.get(host, 'ifaliasoid')
                h.ifaliasoid = self.oidMgr.newOid(
                        'IfAlias',
                        tuple([int(s) for s in ifaliasoidname.split('.')]),
                        'ifalias')
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
            if self.hostsconfig.has_option(host, 'oidset'):
                h.oidset = self.hostsconfig.get(host, 'oidset')
            else:
                # oids to get -- high res. (HC) by default:
                if self.hostsconfig.has_option(host, 'hc'):
                    if self.hostsconfig.get(host, 'hc') in ('off', '0'):
                        h.oidset = 'small_default'
                    else:
                        h.oidset = 'default'
                else:
                    h.oidset = 'default'

            h.oids = self.oidMgr.sets[h.oidset]

            # index increment -- some devices' indexes need to be [in|de]cremented,
            # to sync indexes between tables:
            if self.hostsconfig.has_option(host, 'indinc'):
                h.indexinc = int(self.hostsconfig.get(host, 'indinc'))
            else:
                h.indexinc = 0

            h.results = []
            for o in h.oids:
                h.results.append(dict())
                
            h.perfbase = self.perfbase
            #--------------------------------------------

            # create cmdgen.AsynCommandGenerator() for this host:
            h.asynCommandGenerator()

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
                    for i in range(int(dsv[0]), int(dsv[1])+1):
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
    cw = configWorker('config.ini')

    cw.printHosts()

#
# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
