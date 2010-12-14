#!/usr/bin/python
#
#

import os
import sys

import re

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


form = cgi.FieldStorage()

ifdescr = form.getvalue('ifdescr')


print 'Content-type: text/html\n'
print """
<HEAD>
    <STYLE type="text/css">
        SPAN.gray {
            color: #bbbbbb;
        }
        /* A {
            font-family: 'Fixed', 'Courier';
        } */
        TD {
            border-left:  none;
            border-right: none;
            padding: 0 7 0 7;
        }
    </STYLE>
    <TITLE>SPyBG -- SNMP Bulk Grapher</TITLE>
</HEAD>
<BODY>
"""


#
# Read main config file:
config = 'tg_config.ini'

mainConfig = ConfigParser.ConfigParser()
mainConfig.read(config)


# cisco, but not switches
# (can not do 'show int status'):
cisconotswitches = [ 'Big', 'BigC', 'BigD', 'Small' ]

#
# where all devices have their dirs:
rrddir = mainConfig.get('rrd', 'dir')
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

    dev.picturepath = picturepath

    devices.append(dev)


devices.sort()


#
# HTML page here:
#

print """
<H1><A href="%s">SPyBG Devices</A></H1>
<H2>Find interface by decription:</H2>
""" % 'tg.py'

print """
<FORM>
    <INPUT type="text" name="ifdescr" value="%s">
    <INPUT type="submit">
</FORM>
""" % (ifdescr or '')



showintlink = """,
<A href="http://localwiki/pcgi-bin/showintstatus.py?host=%s&submit=Show+int+status">show int status</A>"""


DEVHEADER = """
<B style="font-size: 130%%;">%s</B><BR>
<TT>(<A href="tg.py?device=%s">bps</A></TT>,
<TT><A href="tg.py?device=%s&what=pps">pps</A>%s)</TT>
"""

RESULT = """
   %s&nbsp;&mdash; <B>%s</B>
   <TT>(<A href="tg.py?device=%s&iface=%s">bps</A></TT>,
   <TT><A href="tg.py?device=%s&iface=%s&what=pps">pps</A>)</TT>
"""


lastdev = None

if ifdescr:

    print '<HR>'
    ifre = re.compile(ifdescr, re.IGNORECASE)

    print '<TABLE border="1">'

    for d in devices:

        for (index, descr) in d.ifaliases:

            searchDescr = ifre.search(descr)

            if searchDescr:

                if lastdev != d.hostname:
                    print '<TR><TD valign="top">'
                    print DEVHEADER % (
                            d.hostname,
                            d.hostname,
                            d.hostname,
                            (d.vendor == 'cisco' and not d.hostname in cisconotswitches) \
                                    and (showintlink % d.ip ) or '',
                        )
                else:
                    print '<TR><TD style="border-top:none;">&nbsp;'

                print '<TD valign="top">'

                print RESULT % (
                        d.ifacesDict[index],
                        descr,
                        d.hostname,
                        index,
                        d.hostname,
                        index
                    )

                lastdev = d.hostname

    print '</TABLE><BR>'

