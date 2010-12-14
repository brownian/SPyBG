#!/usr/bin/python
#
#

import os, sys

import cgi
import cgitb; cgitb.enable()

import ConfigParser

import rrdtool

from spybg import commonFuncs


class device:
    def __init__(self, name):
        self.name = name
        self.ip = None
        self.ifacesDict = None
        self.ifaliasesDict = None

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def printAsDict(self):
        return {
            'name': self.name,
            'hostname': self.hostname,
            'ip': self.ip
        }


def getDevByName(devList, name):
    for d in devList:
        if d.hostname == name:
            return d
    return None


def drawHealth(picname, rrdfile,
        start=-86400, end='now', title=None, w=450, h=100, what=''):
    """Returns path to pic or None."""
    #
    # common:
    graphargs = [
                picname,
                '-l 0',
                '-s %i' % start,
                '-e %s' % str(end),
                '-v %s' % what,
                '-w %i' % w,
                '-h %i' % h,
        ]
    #
    # if title:
    if title:
        graphargs.append('-t %s' % title)
    #
    # defs:
    graphargs.extend ( [
            'DEF:total=%s:total:AVERAGE' % rrdfile,
            'DEF:snmp=%s:snmp:AVERAGE' % rrdfile,
            'DEF:devices=%s:devices:AVERAGE' % rrdfile,
            'DEF:errors=%s:errors:AVERAGE' % rrdfile,
            'CDEF:ntotal=total,140,GT,NaN,total,IF',
            'CDEF:nsnmp=snmp,140,GT,NaN,snmp,IF',
            'LINE1:devices#4444ff:Devices\:',
            'GPRINT:devices:MAX:    %lg\l',
            'LINE1:ntotal#888888:Total time\:',
            'GPRINT:ntotal:AVERAGE: %lg avg,',
            'GPRINT:ntotal:MAX:%lg max\l',
            'LINE1:nsnmp#dd0000:SNMP time\:',
            'GPRINT:nsnmp:AVERAGE:  %lg avg,',
            'GPRINT:nsnmp:MAX:%lg max\l',
            'LINE1:errors#000000:SNMP errors\:',
            'GPRINT:errors:AVERAGE:%lg avg,',
            'GPRINT:errors:MAX:%lg max',
        ] )

    try:
        rrdtool.graph ( *graphargs )
    except Exception, why:
        print 'Exception: %s<BR>' %why
        #print picname, rrdfile
        return None

    return picname



def drawDeviceHealth(picname, rrdfile,
        start=-86400, end='now', title=None, w=450, h=100, what=''):
    """Returns path to pic or None."""
    #
    # common:
    graphargs = [
                picname,
                '-l 0',
                '-s %i' % start,
                '-e %s' % str(end),
                '-v %s' % what,
                '-w %i' % w,
                '-h %i' % h,
        ]
    #
    # if title:
    if title:
        graphargs.append('-t %s' % title)
    #
    # defs:
    graphargs.extend ( [
            'DEF:snmp=%s:snmp:AVERAGE' % rrdfile,
            'DEF:errors=%s:errors:AVERAGE' % rrdfile,
            'LINE1:snmp#dd0000:SNMP time\:',
            'GPRINT:snmp:AVERAGE:  %lg avg,',
            'GPRINT:snmp:MAX:%lg max\l',
            'LINE1:errors#000000:SNMP errors\:',
            'GPRINT:errors:AVERAGE:%lg avg,',
            'GPRINT:errors:MAX:%lg max',
        ] )

    try:
        rrdtool.graph ( *graphargs )
    except Exception, why:
        print 'Exception: %s<BR>' %why
        #print picname, rrdfile
        return None

    return picname



form = cgi.FieldStorage()

targetdevice = form.getvalue('device')

# cisco, but not switches
# (can not do 'show int status'):
cisconotswitches = [ 'Big', 'BigC', 'BigD' ]


print 'Content-type: text/html\n'
print """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HEAD>
    <STYLE type="text/css">
        SPAN.gray {
            color: #bbbbbb;
        }
        TD {
            padding: 0 5 0 5;
        }
    </STYLE>
    <TITLE>System Status : SPyBG -- SNMP Bulk Grapher</TITLE>
    <link rel="icon" type="image/png" href="http://localwiki/favicon.png">
</HEAD>
<BODY>
"""


#
# Read main config file:
config = 'tg_config.ini'

mainConfig = ConfigParser.ConfigParser()
mainConfig.read(config)


#
# where all devices have their dirs:
rrddir = mainConfig.get('rrd', 'dir')
perfbase = mainConfig.get('rrd', 'perfbase')
#
# where (with no path, only filename) iface names and aliases, some
# other info stored:
ifacesfile = mainConfig.get('rrd', 'ifaces')

#
# path to where pictures should be stored to:
picturepath = mainConfig.get('cgi', 'pictures')


# read list of subdirs (list of devices actually)
# (exclude picturepath if subdir of rrddir)
rrdsubdirs = [ x for x in os.listdir(rrddir)
                        if os.path.isdir('%s/%s' % (rrddir, x))
                            and
                        ('/%s' %x) != picturepath.replace(rrddir, '') ]

#
# Make list of devices:
devices = []

for subd in rrdsubdirs:
    dev_ifacesfile = '%s/%s/%s' % (rrddir, subd, ifacesfile)
    #
    if not os.access(dev_ifacesfile, os.F_OK):
        continue

    ifacesConfig = ConfigParser.ConfigParser()
    ifacesConfig.read ( dev_ifacesfile )
    #
    dev = device(ifacesConfig.get('global', 'name'))

    dev.ip = ifacesConfig.get('global', 'ip')

    if ifacesConfig.has_option('global', 'vendor'):
        dev.vendor = ifacesConfig.get('global', 'vendor')
    else:
        dev.vendor = None

    dev.hostname = commonFuncs.cleanHostdirName(dev.name)
    dev.ifacesfile = dev_ifacesfile

    dev.ifaces = ifacesConfig.items('ifnames')
    dev.ifacesDict = dict(dev.ifaces)
    dev.ifaliases = ifacesConfig.items('ifaliases')
    dev.ifaliasesDict = dict(dev.ifaliases)

    # dev.picturepath = picturepath

    dev.perfbase = '%s/%s/%s' % ( rrddir, dev.hostname, perfbase )

    devices.append(dev)


devices.sort ()


#
# HTML page here:
#


#showintlink = """<A
#href="http://localwiki/pcgi-bin/showintstatus.py?host=%s&submit=Show+int+status"
#target="_blank" title="Show int status">%s</A>
#"""

if not targetdevice:
    #
    # show overall status,
    # and every device's status (within a table):
    #
    pic = drawHealth (
            '%s/ALL_perf.png' % ( picturepath ),
            '%s/%s' % ( rrddir, perfbase ),
            title='System Status',
            start=-604800,
            h=150, w=600
        )

    # table with devices:
    print """
    <TABLE border="0">
    <TR><TD><H1><A href="tg.py?">SPyBG Devices</A></H1><BR>
        <TD align="right">
            Total %i devices, (some about) %i interfaces.<BR>
            <B><A href="tg_findiface.py">Find interface by description</A></B>
            <!-- (under development&hellip;) -->

    <TR>
     <TD colspan="2" align="center">
      <A href="?device=System+Status">
        <IMG src="%s"></A>
    <TR>
     <TD valign="top">
    """ % (
            len(devices),
            sum( [ len(x.ifaliases) for x in devices ] ),
            '/%s/%s' % (
                    os.path.basename ( picturepath ),
                    os.path.basename ( pic )
                )
          )


    #
    # total devices and a half of them:
    dleng = len ( devices )
    dhalf = int ( dleng / 2 ) + dleng % 2

    # left column:
    print """
    <TABLE border="1">
    """

    # first half:
    for i in range ( dhalf ):
        pic = drawDeviceHealth (
                '%s/%s_perf.png' % ( picturepath, devices[i].hostname ),
                devices[i].perfbase,
                title='%s' % devices[i].hostname,
                start=-604800
            )

        if pic:
            print """
               <TR valign="top">
               <TD valign="top"><B>%s</B><BR>
                 <A href="?device=%s">
                    <IMG src="%s"></A>
            """ % (
                    devices[i].hostname,
                    devices[i].hostname, '/%s/%s' % (
                        os.path.basename(picturepath),
                        os.path.basename(pic)
                    )
                  )

    # right column:
    print """
    </TABLE>
     <TD valign="top">
     <TABLE border="1">
    """
    # second half:
    for i in range ( dhalf, dleng ):
        pic = drawDeviceHealth (
                '%s/%s_perf.png' % ( picturepath, devices[i].hostname ),
                devices[i].perfbase,
                title='%s' % devices[i].hostname,
                start=-604800
            )

        if pic:
            print """
               <TR valign="top">
               <TD valign="top"><B>%s</B><BR>
                 <A href="?device=%s">
                    <IMG src="%s"></A>
            """ % (
                    devices[i].hostname,
                    devices[i].hostname, '/%s/%s' % (
                        os.path.basename(picturepath),
                        os.path.basename(pic)
                    )
                  )


    print """</TABLE></TABLE> """ 

#
# Some device choosen:
#
else:

    tranges = {
            7200: 'Two hours',
            43200: 'Twelve hours',
            86400: 'One day',
            604800: 'One week',
            2592000: 'One month',
            31536000: 'One year'
        }

    trkeys = tranges.keys()
    trkeys.sort()

    if targetdevice == 'System Status':
        TARGETname = 'System Status'
        TARGEThostname = 'System_Status'
        rrdbase = '%s/%s' % ( rrddir, perfbase )
        drawFunc = drawHealth

    else:
        targetDEVICE = getDevByName(devices, targetdevice)

        if not targetDEVICE:
            print '<H2>Invalid device input.</H2>'
            sys.exit(1)

        TARGETname = targetDEVICE.name
        TARGEThostname = targetDEVICE.hostname

        rrdbase = '%s/%s/%s' % ( rrddir, TARGEThostname, perfbase )
        drawFunc = drawDeviceHealth


    print '<H1><A href="tg.py?">SPyBG Devices</A></H1>\n<TABLE border="0">\n'

    print """<TR><TD align="left" valign="top">
        <H2>%s</H2>
      <TD align="right" valign="top">
    """ % TARGETname

    for start in trkeys:
        #
        picname = '%s/%s_perf_%i.png' % (
                picturepath,
                TARGEThostname,
                start
            )
        #
        pic = drawFunc (picname, rrdbase, start=-start, title=None, w=450, h=100)

        if pic:
            print '<TR><TD colspan="2"><B>%s:</B><BR>' % ( tranges[start] )
            print '<IMG src="/%s/%s"><BR><BR>' % (
                    os.path.basename(picturepath),
                    os.path.basename(picname)
                )

    print '</TABLE>'

print """
    <BR><HR>
    %s
    &bull; <a href="tg_status.py">SPyBG Health Status</a>
    <BR>
    <BR>
""" % (targetdevice and (targetdevice != 'System Status') and
    '&bull; <a href="tg.py?device=%s">This device\'s traffic</a>' % TARGEThostname
        or '')


