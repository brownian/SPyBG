#
#
#

import os
import ConfigParser
import rrdtool

import psycopg2
from psycopg2.extensions import adapt

from datetime import datetime

from spybg import commonFuncs, snmpAgent


step = '120'
hbeat = '200'
min = '0'
max = '1250000000'       # 10Gig

DS = 'DS:%s:COUNTER:%s:%s:%s'

# RRA:AVERAGE:0.5:1:600                                 # 5 minute samples, 50h
# RRA:MAX:0.5:1:600                                     # 5 minute samples
# RRA:AVERAGE:0.5:6:600                                 # 30 minute samples, 300h, 12d
# RRA:MAX:0.5:6:600                                     # 30 minute samples
# RRA:AVERAGE:0.5:24:600                                # 2 hour samples, 1200h, 50d
# RRA:MAX:0.5:24:600                                    # 2 hour samples
# RRA:AVERAGE:0.5:288:732                               # 1 day samples, 732d
# RRA:MAX:0.5:288:732                                   # 1 day samples

RRAcreateparams = (
        # "last two hours":
        'RRA:AVERAGE:0.5:1:90',     # 90x2-min samples, 3h
        'RRA:MAX:0.5:1:90',
        # "last 12 hours":
        'RRA:AVERAGE:0.5:3:150',    # 6-min samples, 12+3h
        'RRA:MAX:0.5:3:150',
        # "last day":
        'RRA:AVERAGE:0.5:6:195',    # 12-min samples, 24+15h
        'RRA:MAX:0.5:6:195',
        # "last week":
        'RRA:AVERAGE:0.5:42:165',   # 84-min samples, 8*24+24+15h
        'RRA:MAX:0.5:42:165',
        # "last month":
        'RRA:AVERAGE:0.5:168:170',  # 336-min samples, 38*24+24+15h
        'RRA:MAX:0.5:168:170',
        # "last year":
        'RRA:AVERAGE:0.5:2016:178', # 4032-min samples, 38*24*13+24+15h
        'RRA:MAX:0.5:2016:178',
    )


#
# Create performance base:
#

def createPerfBase(dir, name):
    rrdbase = '%s/%s' % (dir, name)
    if os.access(rrdbase, os.F_OK):
        return

    try:
        rrdtool.create(
                        rrdbase,
                        '-s %s' % step,
                        *(
                            (
                                'DS:%s:GAUGE:%s:%s:%s' % ('total', hbeat, min, max),
                                'DS:%s:GAUGE:%s:%s:%s' % ('snmp', hbeat, min, max),
                                'DS:%s:GAUGE:%s:%s:%s' % ('devices', hbeat, min, max),
                                'DS:%s:GAUGE:%s:%s:%s' % ('ports', hbeat, min, max),
                                'DS:%s:GAUGE:%s:%s:%s' % ('errors', hbeat, min, max)
                            ) + RRAcreateparams
                         )
                      )
    except:
        # should go in log?
        print 'ERROR: Can not create %s.' % rrdbase
        raise

def createHostPerfBase(dir, name):
    rrdbase = '%s/%s' % (dir, name)

    if os.access(rrdbase, os.F_OK):
        return

    try:
        rrdtool.create(
                        rrdbase,
                        '-s %s' % step,
                        *(
                            (
                                'DS:%s:GAUGE:%s:%s:%s' % ('snmp', hbeat, min, max),
                                'DS:%s:GAUGE:%s:%s:%s' % ('errors', hbeat, min, max)
                            ) + RRAcreateparams
                        )
                      )
    except:
        # should go in log?
        print 'ERROR: Can not create %s.' % rrdbase
        raise


def checkConfig(dir):
    if not ( os.access(dir, os.F_OK) and os.access(dir, os.W_OK) ):
        # should go to log?..
        print 'Error: %s is not exists or not writable.' % dir
        return False
    else:
        return True


def checkBase(host):
    """Checks RRD base existence.

    Returns None if RRD base for any interface
    does not exist or not writable;
    returns path to hostdir if it's OK.

    Does not check validity of RRD base.
    """

    hostdir = host.hostdir

    #
    # Check hostdir:
    #
    if not os.access(hostdir, os.F_OK):
        # try to create
        try:
            os.mkdir(hostdir)
        except OSError:
            # should go to log?..
            print 'Error: can not create %s.' % hostdir
            return None

    elif not os.access(hostdir, os.W_OK):
        # not writable
        # should go to log?..
        print 'Error: %s in not writable.' % hostdir
        return None

    #
    # check/create RRD base:
    #
    # get descrs:
    host.getIfNames()

    #
    # For every key in ifnamesDict
    # an RRD base should exist.
    #
    for index, ifname in host.ifnamesDict.items():
        ifname = str(ifname)
        rrdbase = '%s/%s.rrd' % (hostdir, ifname)

        # replace '/' in interface name:
        rrdbase = rrdbase.replace(
                ifname,
                commonFuncs.cleanIfName(ifname))

        # is rrdbase exist?
        if os.access(rrdbase, os.F_OK):
            # is it writable?
            if not os.access(rrdbase, os.W_OK):
                print 'Not writable %s' % rrdbase
                return None
        else:
            # try to create rrdbase for iface `key':
            # print "try to create rrdbase %s for iface `%s'" % \
            #                 (rrdbase, ifnamesDict[key])

            #
            # Collect DSs for this port:
            #
            allDS = ()
            lOids = host.oids
            #
            # sort oids to guarantee proper o.alias's order:
            lOids.sort(commonFuncs.sortOids)
            for o in lOids:
                allDS = allDS + ( DS % (o.alias, hbeat, min, max) ,)

                # print (allDS + RRAcreateparams)
            try:
                rrdtool.create(
                                rrdbase,
                                '-s %s' % step,
                                *(allDS + RRAcreateparams)
                              )
            except:
                # should go in log?
                print 'ERROR: Can not create %s.' % rrdbase
                return None

    return hostdir



def snmpResult2RRD(host, dOid_to_Res):

    lDsNames = []

    lOids = dOid_to_Res.keys()
    #
    # sort oids to guarantee proper o.alias's order:
    lOids.sort(commonFuncs.sortOids)

    for o in lOids: 
        lDsNames.append(o.alias)


    for index, ifname in host.ifnamesDict.items():

        lDsValues = []

        for o in lOids:
            # if index in dOid_to_Res[o].keys():
            if dOid_to_Res[o].get(index):
                value = dOid_to_Res[o][index]
            else:
                #
                # Arggh! Some HC tables may not contain
                # some indexes.
                value = 'U'

            lDsValues.append(value)

        # try to update RRD base:
        # template = ':'.join(lDsNames)
        updstr = 'N:%s' % ':'.join(lDsValues)

        rrdbase = '%s/%s.rrd' % (
                            host.hostdir,
                            commonFuncs.cleanIfName(ifname)
                        )

        try:
            rrdtool.update(
                            rrdbase,
                            updstr
                          )
        #except:
        #       print "Error in update (%s, %s)" % (host.hostname, iface)
        except Exception, why:
            print "Error in update (%s, %s) - %s" % (
                            host.hostname,
                            index,
                            why )
            # raise


    return True


def snmpResult2RRD2(host):
    connection = psycopg2.connect(
                host='10.0.10.111', port=54321, database='GIS_2010',
                user='macswriter', password='macswriter'
            )

    cursor = connection.cursor()

    dOid_to_Res = dict()

    for i, o in enumerate(host.oids):
        dOid_to_Res[o] = host.results[i]

    data = {}

    for oid, results in dOid_to_Res.items():
        for port, result in results.items():
            if data.get(port, None):
                data[port][oid.name] = int(result)
            else:
                data[port] = { oid.name: int(result) }


    for port, values in data.items():
        insert = "INSERT INTO netstats.traf (%s) VALUES (%s)"
        query = insert % (
                            ', '.join([ '"%s"' % col for col in
                                    ['dev_name', 'port'] \
                                    + values.keys() \
                                    + ['inserted',]
                                ]),
                            ', '.join(
                                    [adapt(host.hostname).getquoted(), str(port)] \
                                    + [str(adapt(v)) for v in values.values()] \
                                    # + ['now()',]
                                    + ["'%s'" % datetime.now(),]
                                )
                        )
        cursor.execute(query)
        # print query

    connection.commit()
    cursor.close()
    connection.close()

    rrdbase = '%s/%s'  % (host.hostdir, host.perfbase)
    updstr = 'N:%s:%s' % (host.snmptime, host.errors)
    #sys.stderr.write('%s, %s\n' % (rrdbase, updstr))
    #sys.stderr.flush()

    try:
        rrdtool.update(rrdbase, updstr) 
    except Exception, why:
        print "Error in update (%s, %s) - %s" % (
                            host.hostname,
                            index,
                            why )

    return True


def snmpResult2RRD3(host):
    dOid_to_Res = dict()

    for i, o in enumerate(host.oids):
        dOid_to_Res[o] = host.results[i]

    lOids = dOid_to_Res.keys()
    #
    # sort oids to guarantee proper o.alias's order:
    lOids.sort(commonFuncs.sortOids)


    inioverride = '%s/%s.override' % (host.hostdir, host.ifacesfile)

    if os.access(inioverride, os.F_OK):
        ifnamesOverride = ConfigParser.ConfigParser()
        ifnamesOverride.read(inioverride)
        ifnamesPairs = [ (int(index), value)
                for index, value in ifnamesOverride.items('ifnames') ]
    else:
        ifnamesPairs = host.ifnamesDict.items()


    for index, ifname in ifnamesPairs:

        lDsValues = []

        for o in lOids:
            # if index in dOid_to_Res[o].keys():
            if dOid_to_Res[o].get(index):
                value = dOid_to_Res[o][index]
            else:
                #
                # Arggh! Some HC tables may not contain
                # some indexes.
                value = 'U'

            lDsValues.append(value)

        # try to update RRD base:
        # template = ':'.join(lDsNames)
        updstr = 'N:%s' % ':'.join([str(v) for v in lDsValues])

        rrdbase = '%s/%s.rrd' % (
                            host.hostdir,
                            commonFuncs.cleanIfName(ifname)
                        )

        try:
            rrdtool.update(
                            rrdbase,
                            updstr
                          )
        #except:
        #       print "Error in update (%s, %s)" % (host.hostname, iface)
        except Exception, why:
            print "Error in update (%s, %s) - %s" % (
                            host.hostname,
                            index,
                            why )

    rrdbase = '%s/%s'  % (host.hostdir, host.perfbase)
    updstr = 'N:%s:%s' % (host.snmptime, host.errors)
    #sys.stderr.write('%s, %s\n' % (rrdbase, updstr))
    #sys.stderr.flush()

    try:
        rrdtool.update(rrdbase, updstr) 
    except Exception, why:
        print "Error in update (%s, %s) - %s" % (
                            host.hostname,
                            index,
                            why )

    return True
#
#
# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
