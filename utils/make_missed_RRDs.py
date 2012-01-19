#!/usr/bin/env python

import sys,os
import rrdtool

import ConfigParser

from spybg import commonFuncs, configWorker, snmpResult2RRD

try:
    ini = sys.argv[1]
except IndexError:
    print "Specify ini file name"
    sys.exit(1)

config = ConfigParser.ConfigParser()
config.read(ini)


allDS = ()
lOids = configWorker.HCoids
lOids.sort(commonFuncs.sortOids)

for o in lOids:
    allDS = allDS + ( snmpResult2RRD.DS % (
                        o.alias,
                        snmpResult2RRD.hbeat,
                        snmpResult2RRD.min,
                        snmpResult2RRD.max)
                    ,)


for index, fname in config.items('ifnames'):

    rrdbase = '%s.rrd' % fname

    if os.access(rrdbase, os.F_OK):
        print "%s exists, skipping..." % rrdbase
        continue

    print "Trying to create %s..." % rrdbase,
    try:
        rrdtool.create(rrdbase,
                       '-s %s' % snmpResult2RRD.step,
                       *(allDS + snmpResult2RRD.RRAcreateparams)
                      )
    except Exception, why:
        # what we may want to do here?-)
        # raise
        print "Could not create %s: %s\n\n" % (rrdbase, why)
    else:
        print "done"

# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
