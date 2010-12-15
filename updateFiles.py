#!/usr/bin/python -u
#
#

import os
import sys

import getopt

from pysnmp.entity.rfc3413.oneliner import cmdgen


import ConfigParser

from spybg import commonFuncs, snmpAgent, configWorker, snmpResult2RRD

execfile('Zyxels-STUPID.py')

# default mode:
mode = 'ini'

targetdev = None

# Initialize help messages
options = """Options:
    -h --help          this help message,
    -i --ini           refresh INI files only (default),
    -b --bases         check/create RRD bases only,
    -a --do-all        do all (both INI and RRD),
    --device DEVICE            device name to proceed.
"""

usage = 'Usage: %s [options] --devive DEVICE\n' % sys.argv[0]
usage = usage + options

try:
    (opts, args) = getopt.getopt (
            sys.argv[1:], 'hiba', \
            [ 'help', 'ini', 'bases', 'do-all', 'device=' ]
        )
except getopt.error, why:
    print '\ngetopt error: %s\n\n%s' % (why, usage)
    sys.exit(-1)

try:
    for opt in opts:
        if opt[0] == '-h' or opt[0] == '--help':
            print usage
            sys.exit(0)
        
        if opt[0] == '-i' or opt[0] == '--ini':
            mode = 'ini'

        if opt[0] == '-b' or opt[0] == '--bases':
            mode = 'bases'

        if opt[0] == '-a' or opt[0] == '--do-all':
            mode = 'do-all'

        if opt[0] == '--device':
            targetdev = opt[1]

except ValueError, why:
    print 'Bad parameter \'%s\' for option %s: %s\n%s' \
          % (opt[1], opt[0], why, usage)
    sys.exit(-1)

if len(opts) == 0:
    mode = 'ini'


if not targetdev:
    print '\nTarget device not specified.\n\n%s' % usage
    print '\n Run\n\t%s --device HELP\n to get possible devices names.\n' % sys.argv[0]
    sys.exit(1)


#
# Working:
#

cw = configWorker.configWorker('config.ini')

alldevs = [
        commonFuncs.cleanHostdirName ( h.hostname )
            for h in cw.hosts
    ]


if targetdev not in alldevs:
    # print them sorted:
    alldevs.sort()
    if not targetdev in ('HELP', 'ALL'):
        # nor HELP, neither ALL:
        print 'No such device: %s.' % targetdev 
    elif targetdev == 'HELP':
        # HELP:
        print 'Possible devices are:\n%s\n' %  ', '.join ( alldevs )
    else:
        # ALL:
        print 'Working for ALL devices (%i total).\n\n' % len ( alldevs )


#
for host in cw.hosts:

    cleanedhostname = commonFuncs.cleanHostdirName(host.hostname)

    if targetdev and not (targetdev in (cleanedhostname, 'ALL')):
        continue

    try:
        host.getIfNames ( )
    except Exception, why:
        print 'Host %s: cannot get table: %s' % (host.hostname, why)


    host.hostdir = '%s/%s' % (cw.rrdhostdir, cleanedhostname)

    if not os.access(host.hostdir, os.F_OK):
        # try to create
        try:
            os.mkdir(host.hostdir)
        except OSError:
            # should go to log?..
            print 'Error: can not create %s.' % host.hostdir
            sys.exit(-1)

    #
    # INI:
    #
    if mode in ('ini', 'do-all'):
        sys.stdout.write (
                'Creating/refreshing INI file for %s... ' % host.hostname
            )
        sys.stdout.flush()

        # store ifnames into ini:
        ifnamesConfig = ConfigParser.ConfigParser()

        ifnamesConfig.add_section('global')
        ifnamesConfig.set('global', 'name', host.hostname)
        ifnamesConfig.set('global', 'ip', host.ip)
        # ifnamesConfig.set('global', 'hc', host.hc)
        ifnamesConfig.set('global', 'oidset', host.oidset)
        ifnamesConfig.set(
                'global',
                'ports',
                host.ports and ','.join ( [ str(x) for x in host.ports ] ) or ''
            )

        ifnamesConfig.add_section('ifnames')
        for ifname in host.ifnamesDict.keys():
            ifnamesConfig.set (
                    'ifnames',
                    str(ifname),
                    host.ifnamesDict[ifname]
                )
        #
        # Get ifaliases' oid and ifaliases:
        if not host.ifaliasoid:
            try:
                (vendor, ifa_oid) = configWorker.getAliasOid(host)
            except TypeError:
                print "\nError grabbing info from %s, skipping...\n" % host.hostname
                cw.hosts.remove(host)
                print configWorker.getAliasOid(host)
                raise
                continue
        else:
            (vendor, ifa_oid) = ('unkn', host.ifaliasoid)

        ifnamesConfig.set('global', 'vendor', vendor)

        if ifa_oid:
            ifaliasesDict = dict()

            host.getTables (
                    oids=[ifa_oid],
                    results=[ifaliasesDict],
                    iftable=False               # that's not an ifaces table.
                )

            ifnamesConfig.add_section('ifaliases')

            for ifindex in ifaliasesDict.keys():
                #
                # Stupid ZyXEL shifts indexes in enterprize three:
                if (vendor in ('zyxel', 'unkn')) and (host.ip in stupidZyxels):
                    index = ifindex + 1
                else:
                    index = ifindex
                ifnamesConfig.set (
                        'ifaliases',
                        str(index),
                        ifaliasesDict[ifindex]
                    )

        #
        # Write to file:
        #
        # configfile = open ('%s/ifaces.ini' % host.hostdir, 'w')
        configfile = open ('%s/%s' % (host.hostdir, host.ifacesfile), 'w')
        ifnamesConfig.write(configfile)
        configfile.close()

        sys.stdout.write ('done.\n')
        sys.stdout.flush()


    #
    # BASES:
    #
    if mode in ('bases', 'do-all'):
        sys.stdout.write (
                'Creating/checking RRD bases for %s... ' % host.hostname
            )
        sys.stdout.flush()

        #
        # snmpResult2RRD.checkBase(host, ports, oids) returns None
        # if error in checking/creating rrdbase,
        # or path to switch's directory (where rrd for every port
        # are located):
        # 
        rrdcheckresult = snmpResult2RRD.checkBase ( host )

        # If check fails, remove host from list
        # of hosts to be processed:
        if not rrdcheckresult:
            sys.stdout.write (
                    "Should remove %s, check failed. " % host.hostname
                )
            sys.stdout.flush()

            cw.hosts.remove(host)

        #
        # if rrdcheckresult:
        else:
            snmpResult2RRD.createHostPerfBase(host.hostdir, cw.perfbase)

        sys.stdout.write ('done.\n')
        sys.stdout.flush()


#
# create/check common perf.rrd:
if mode in ('bases', 'do-all') and targetdev in (None, 'ALL'):
    snmpResult2RRD.createPerfBase(cw.rrdhostdir, cw.perfbase)
