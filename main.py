#!/usr/bin/python
#
#
# A lot of info (as for me,) here:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
#
# How about that?..
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/302746
#
# +++ !
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/203871
#

import sys, os, time, traceback, signal, threading

from datetime import datetime, timedelta

import ConfigParser, rrdtool

import dae

from pyasn1.type.error import PyAsn1Error

import goodthreads


from spybg import commonFuncs, configWorker, snmpResult2RRD


def signalHandler(signum, frame):
    global cw, doReconfig, doExit

    if signum == signal.SIGHUP:
        doReconfig = 1

    elif signum == signal.SIGTERM:
        doReconfig = 0
        doExit = 1


def doGet(host):
    global totalports, totPortsLock
    #
    host.errors = 0
    host.snmptime = 0.0

    # host.getTables()
    try:
        host.getTables()
    except PyAsn1Error:
        pass

    #
    totPortsLock.acquire()
    totalports += max([ len(x) for x in host.results ])
    totPortsLock.release()

    return host


config_ini = 'config.ini'


#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
#
if __name__ == '__main__':


    if len(sys.argv) > 1:
        workdir = sys.argv[1]
        try:
            os.chdir(workdir)
        except Exception, why:
            print 'Can not chdir to %s: %s' % (workdir, why)
            sys.exit(-1)
    else:
        workdir = os.getcwd()


    # hook signals:
    signal.signal(signal.SIGTERM, signalHandler)
    signal.signal(signal.SIGHUP, signalHandler)
    
    # start working (go to background):
    dae.startstop(dir=workdir, stdout='test.out', stderr='test.err')


    cw = configWorker.configWorker(config_ini)
    c_fd = open(cw.hostsfile)
    c_mt = os.fstat(c_fd.fileno()).st_mtime

    totPortsLock = threading.Lock()
    totalports = 0
    doReconfig = None

    #if cw.doDae == 'yes':
    #    doExit = False
    #else:
    #    doExit = True
    doExit = False

    run = 1

    while 1:

        sys.stdout.write ( '(run %i:) %s: ' % ( run, datetime.now() ) )
        sys.stdout.flush ()
        
        totalports = 0
        t1 = datetime.today()

        # re-allocate pool every run:
        th_pool = goodthreads.ThreadPool(cw.maxthreads)

        for h in cw.hosts:
            # th_pool.queueTask(doGet, h, snmpResult2RRD.snmpResult2RRD)
            # th_pool.queueTask(doGet, h, snmpResult2RRD.snmpResult2RRD2)
            th_pool.queueTask(doGet, h, snmpResult2RRD.snmpResult2RRD3)

        #
        # wait until finished:
        th_pool.joinAll()

        #
        # Collect variables and update perf. RRD:
        #
        # total errors number:
        toterrors = sum([ h.errors for h in cw.hosts ])

        # total errors number:
        totsnmptime = (sum(
                    [ h.snmptime for h in cw.hosts ]
                ) + 0.0)/cw.maxthreads

        t2 = datetime.today()

        # time spent for this one run:
        tottime = commonFuncs.timedelta2secs(t2 - t1)

        # try to update perf. rrd:
        updstr = 'N:%s:%s:%s:%s:%s' % (
                tottime, totsnmptime, len(cw.hosts), totalports, toterrors
            )

        rrdtool.update(
                '%s/%s' % (cw.rrdhostdir, cw.perfbase),
                updstr
            )

        sys.stdout.write(
            '%.3f sec total, %.3f sec SNMP (%i devices, %i ports, %i errors).\n' % (
                        tottime,
                        totsnmptime,
                        len(cw.hosts),
                        totalports,
                        toterrors
                    )
                )
        sys.stdout.flush()


        # FIXME:
        #sys.exit(0)


        #
        # we may sleep for timeleft time:
        timeleft = \
           (120 > int(tottime)) and (120 - int(tottime)) or 0

        for s in range(timeleft):
           # check for doReconfig or doExit requests:
           if doReconfig:

               sys.stderr.write ("%s: Reconfig requested, reloading config... " % datetime.now() )
               sys.stderr.flush()
               cw.hosts = []
               cw.configRead()
               sys.stderr.write("done.\n")
               sys.stderr.flush()

               doReconfig = 0

           elif doExit:
               sys.stderr.write("Exit requested, exited.\n")
               sys.exit(0)

           elif os.fstat(c_fd.fileno()).st_mtime > c_mt:
               sys.stderr.write ("%s: Config file has changed, reloading config... " % datetime.now())
               sys.stderr.flush()
               cw.hosts = []
               cw.configRead()
               sys.stderr.write("done.\n")
               sys.stderr.flush()
               c_mt = os.fstat(c_fd.fileno()).st_mtime

           time.sleep(1)

        run += 1

#
# EOF
