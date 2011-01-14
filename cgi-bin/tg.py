#!/usr/bin/python
#
#

import os
import sys

import cgi
import cgitb; cgitb.enable()

import pickle
import ConfigParser

import rrdtool

from spybg import commonFuncs

import tg_inc


form = cgi.FieldStorage()

targetdevice = form.getvalue('device')

targetiface = form.getvalue('iface')

# what to show (oid_subset name here):
what = form.getvalue('what')

# CF:
cf = form.getvalue('cf') or 'avg'

# logar. or not:
loga = form.getvalue('loga') == 'on' and True or False
logarange = form.getvalue('logarange') or "auto"


# cisco, but not switches
# (can not do 'show int status'):
cisconotswitches = [ 'Big', 'BigC', 'BigD', 'Small' ]
# has ifaces like Gi0/1.<VID>:
ciscorouters = [ 'Big', 'BigC', 'BigD', 'Small', 'C6500' ]

#
#
title = {
    'bps': 'Bits per second',
    'pps': 'Packets per second',
    'bpp': 'Bytes per packet'
}


print 'Content-type: text/html\n'
print """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HEAD>
    <meta http-equiv="Content-type" content="text/html; charset=UTF-8">
    <STYLE type="text/css">
        SPAN.gray {
            color: #bbbbbb;
        }
        TD {
            padding: 0px 5px 0px 5px;
        }
    </STYLE>
    <SCRIPT type="text/javascript">
    function changeRangeList()
    {
        document.getElementById('logarange').disabled = !document.getElementById('loga').checked;
    }
    </SCRIPT>
    <link rel="icon" type="image/png" href="http://localwiki/favicon.png">
"""


#
# Read main config file:
config = 'tg_config.ini'

mainConfig = ConfigParser.ConfigParser()
mainConfig.read(config)


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
    ifacesConfig.read(dev_ifacesfile)
    #
    dev = tg_inc.device(ifacesConfig.get('global', 'name'))

    dev.ip = ifacesConfig.get('global', 'ip')

    if ifacesConfig.has_option('global', 'vendor'):
        dev.vendor = ifacesConfig.get('global', 'vendor')
    else:
        dev.vendor = None

    dev.hostname = commonFuncs.cleanHostdirName(dev.name)

    dev.setname, dev.subsets = \
            pickle.load(
                open('%s/%s/oid_sets.pickle' % (
                        rrddir, dev.hostname)))

    dev.ifacesfile = dev_ifacesfile

    dev.ifaces = ifacesConfig.items('ifnames')
    dev.ifacesDict = dict(dev.ifaces)
    dev.ifaliases = ifacesConfig.items('ifaliases')
    dev.ifaliasesDict = dict(dev.ifaliases)

    dev.picturepath = picturepath

    devices.append(dev)


devices.sort()


dleng = len(devices)
dhalf = int(dleng/2) + dleng%2

#
# HTML page here:
#

#print '<H1><A href="?">SPyBG Devices</A></H1>'


showintlink = """<A
href="http://localwiki/pcgi-bin/showintstatus.py?host=%s&submit=Show+int+status"
target="_blank" title="Show int status">%s</A>
"""


if not targetdevice:
    print """
        <TITLE>SPyBG -- SNMP Bulk Grapher</TITLE>
    </HEAD>
    <BODY>
    """

    print """
    <table border="0">
    <tr><td><h1><a href="?">SPyBG Devices</a></a1><br></td>
        <td align="right">
            <a href="tg_status.py?device=System+Status">~</a>%i devices and %i interfaces total<br>
            <b><b href="tg_findiface.py">Find interface by description</a></b><br>
            <b><b href="tg_aggregate.py">View (or manage?) aggregations</a></b></td></tr>

    <tr><td valign="top">
    """ % ( dleng, sum([ len(x.ifaces) for x in devices ]) )

    def listrow(index):
        thisdev = devices[i]
        return """
           <tr valign="center">
            <td>%i</d>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
           </tr>
        """ % (
                (i + 1),
                thisdev.hostname,
                ', '.join([
                        '<a href="?device=%s&what=%s" title="%s">%s</a>' % \
                            (thisdev.hostname, s, ', '.join(it), s)
                                for s, it in thisdev.subsets.items()
                    ]),
                thisdev.vendor == 'cisco' and
                    not (thisdev.name in cisconotswitches) and
                        showintlink % (thisdev.ip, thisdev.ip) or thisdev.ip
              )


    # left column:
    print """
    <table border="1">
        <tr><th>#</th><th>Name</th><th>What</th><th>Address</th></tr>
    """
    for i in range(dhalf):
        print listrow(i)

    # right column:
    print """
    </table>
    </td>
    <td valign="top">
    <table border="1">
        <tr><th>#</th><th>Name</th><th>What</th><th>Address</th></tr>
    """
    for i in range(dhalf, dleng):
        print listrow(i)

    print """</table>"""


    print """
    </td></tr>
    </table>
    """ 


else:
    # Some device choosen.
    if not targetiface:
        targetDEVICE = tg_inc.getDevByName(devices, targetdevice)

        if not targetDEVICE:
            print '<H2>Invalid device input.</H2>'
            sys.exit(1)

        try:
            S = form.getvalue('S') \
                and int(form.getvalue('S')) or 86400
        except:
            S = 86400

        if not what or not what in targetDEVICE.subsets.keys():
            what = targetDEVICE.subsets.keys()[0]

        print """
            <TITLE>%s : SPyBG -- SNMP Bulk Grapher</TITLE>
        </HEAD>
        <BODY>
        """ % targetDEVICE.hostname

        ifaceskeys = [ int(x) for x in targetDEVICE.ifacesDict.keys() ]

        #################################################################
        # for "ciscorouters":
        #################################################################
        def sortByVlan(key1, key2):
            """ Sorts ifaces by VLAN id.
            
            For every iface name in form of "Gi0/1.3145"
            sorts by VLAN id.
            """
            key1 = str(key1)
            key2 = str(key2)

            if targetDEVICE.ifacesDict[key1]:
                val1 = targetDEVICE.ifacesDict[key1].split('.')
                if len(val1) == 2:
                    vval1 = int(val1[1])
                else:
                    vval1 = None
            else:
                val1 = None
                vval1 = None

            if targetDEVICE.ifacesDict[key2]:
                val2 = targetDEVICE.ifacesDict[key2].split('.')
                if len(val2) == 2:
                    vval2 = int(val2[1])
                else:
                    vval2 = None
            else:
                val2 = None
                vval2 = None

            return cmp(vval1, vval2)
        #
        #################################################################

        if targetDEVICE.hostname in ciscorouters:
            ifaceskeys.sort(sortByVlan)
        else:
            ifaceskeys.sort()

        otherviewlink = """<a href="?device=%s&what=%s%s&cf=%s&S=%s">%s</a>"""

        print '<TABLE border="0">\n'

        print """<TR><TD align="left" valign="top">
            <H2><A href="?">ALL</A>: <A href="?device=%s%s">%s (%s)</A></H2><BR>
          <TD align="right" valign="top">
            <B>%s</B>
        """ % (
                targetDEVICE.hostname,
                loga and '&loga=on' or '',
                targetDEVICE.name,
                targetDEVICE.ip,
                #
                ', '.join([
                    otherviewlink % (
                            targetDEVICE.hostname,
                            what_,
                            loga and '&loga=on' or '',
                            cf,
                            S,
                            what_
                        ) for what_ in targetDEVICE.subsets.keys()
                            if not what_ == what ])
              )

        print """
            <TR><TD colspan="2" align="right">
            <FORM>
                <INPUT type="hidden" name="device" value="%s">
                <INPUT type="hidden" name="what" value="%s">
                <select name="S">
                    <OPTION value="7200"%s>2 hours
                    <OPTION value="86400"%s>1 day
                </select>,
                CF: 
                <SELECT name="cf">
                    <OPTION value="avg"%s>AVERAGE
                    <OPTION value="max"%s>MAX
                </SELECT>, &nbsp;
                Log. scale:
                <INPUT type="checkbox" name="loga" id="loga"
                    onChange="javascript:changeRangeList()"%s>
                <SELECT name="logarange" id="logarange"%s>
                    <OPTION value="auto"%s>full auto
                    <OPTION value="min"%s>0.01 to 1
                    <OPTION value="tiny"%s>0.1 to 10
                    <OPTION value="med"%s>1 to 100
                    <OPTION value="lar"%s>10 to 1000
                    <OPTION value="max"%s>100 to 10000
                </SELECT>
                <INPUT type="Submit" value="ok">
            </FORM>
        """ % (
                    targetDEVICE.hostname,
                    what,
                    S == 7200 and " selected" or "",
                    S == 86400 and " selected" or "",
                    cf == 'avg' and ' selected' or '',
                    cf == 'max' and ' selected' or '',
                    loga and ' checked' or '',
                    loga and ' ' or ' disabled',
                    logarange == "auto" and ' selected' or '',
                    logarange == "min" and ' selected' or '',
                    logarange == "tiny" and ' selected' or '',
                    logarange == "med" and ' selected' or '',
                    logarange == "lar" and ' selected' or '',
                    logarange == "max" and ' selected' or '',
                )


        for i, k in enumerate(ifaceskeys):
            ifaceName = targetDEVICE.ifacesDict.get(str(k))
            ifaceAlias = targetDEVICE.ifaliasesDict.get(str(k))
            ifaceNameCleaned = commonFuncs.cleanIfName(ifaceName)

            rrdb = '%s/%s/%s.rrd' % (
                    rrddir,
                    targetDEVICE.hostname,
                    ifaceNameCleaned
                )

            picshortname = '%s_%s.png' % (
                        targetDEVICE.hostname,
                        ifaceNameCleaned
                    )

            picname = '%s/%s' % (picturepath, picshortname)

            pictitle = '%s: %s' % (
                    ifaceName,
                    ifaceAlias or '(No descr)'
                )
            #
            #
            if not i % 2:
                print '<TR>'

            print '<TD><B>%s: %s</B><BR>' % (
                        ifaceName,
                        ifaceAlias or '<SPAN class="gray">(No descr)</SPAN>'
                    )

            #
            # what to draw (bps, pps...):
            pic = tg_inc.drawPic(targetDEVICE, what, rrdb, picname,
                    title=pictitle, w=450, start=-S,
                    h=100, loga=loga, logarange=logarange, cf=cf)

            if pic:
                print '<a href="?device=%s&iface=%s%s%s&cf=%s&what=%s"><img src="/%s/%s" title="index: %s"></a>' % (
                        targetDEVICE.hostname,
                        k,
                        what == 'pps' and '&what=pps' or '',
                        #
                        loga and '&loga=on' or '',
                        cf,
                        what,
                        #
                        os.path.basename(picturepath),
                        picshortname,
                        k
                    )

        print """</TABLE>
        """


    #
    # Some interface choosen:
    #
    else:
        targetDEVICE = tg_inc.getDevByName(devices, targetdevice)
        ifaceName = targetDEVICE.ifacesDict.get(str(targetiface))
        ifaceAlias = targetDEVICE.ifaliasesDict.get(str(targetiface))
        if ifaceName:
            ifaceNameCleaned = commonFuncs.cleanIfName(ifaceName)
        else:
            targetDEVICE = None

        if not targetDEVICE:
            print '<H2>Invalid device input.</H2>'
            sys.exit(1)

        print """
            <TITLE>%s (%s) : %s : SPyBG -- SNMP Bulk Grapher</TITLE>
        </HEAD>
        <BODY>
        """ % (ifaceName, ifaceAlias, targetDEVICE.hostname)

        #
        # header -- dev. name (link) and switch to "another WHAT":
        print """<TABLE border="0">
        <TR><TD align="left" valign="top">
              <H2><A href="?">ALL</A>: <A href="?device=%s%s&what=%s&cf=%s">%s (%s)</A>:<BR>%s</H2>
        """ % (
                targetDEVICE.hostname,
                loga and '&loga=on' or '',
                what == 'bpp' and 'bps' or what,
                cf,
                targetDEVICE.name,
                targetDEVICE.ip,
                title.get(what, what)
            )

        otherviewlink = """<a href="?device=%s&iface=%s&what=%s%s&cf=%s" title="%s">%s</q>"""

        print """
        <TR><!-- <TD colspan="2"> -->
            <TD>
            <B style="font-size:150%%;">%s: %s</B><BR>
            <TD align="right" valign="top">
              <b>%s</b>
        """ % (
                ifaceName,
                ifaceAlias,
                #
                ', '.join([
                    otherviewlink % (
                            targetDEVICE.hostname,
                            str(targetiface),
                            what_,
                            loga and '&loga=on' or '',
                            cf,
                            what_,
                            what_
                        ) for what_ in targetDEVICE.subsets.keys()
                            if not what_ == what ])
            )


        print """
            <TR><TD colspan="2" align="right">
            <FORM>
                <INPUT type="hidden" name="device" value="%s">
                <INPUT type="hidden" name="iface" value="%s">
                <INPUT type="hidden" name="what" value="%s">
                CF: 
                <SELECT name="cf">
                    <OPTION value="avg"%s>AVERAGE
                    <OPTION value="max"%s>MAX
                </SELECT>, &nbsp;
                Logarithmic:
                <INPUT type="checkbox" name="loga" id="loga"
                    onChange="javascript:changeRangeList()"%s>
                <SELECT name="logarange" id="logarange"%s>
                    <OPTION value="auto"%s>full auto
                    <OPTION value="min"%s>0.01 to 1
                    <OPTION value="tiny"%s>0.1 to 10
                    <OPTION value="med"%s>1 to 100
                    <OPTION value="lar"%s>10 to 1000
                    <OPTION value="max"%s>100 to 10000
                </SELECT>
                <INPUT type="Submit" value="ok">
            </FORM>
        """ % (
                    targetDEVICE.hostname,
                    str(targetiface),
                    what,
                    cf == 'avg' and ' selected' or '',
                    cf == 'max' and ' selected' or '',
                    loga and ' checked' or '',
                    loga and ' ' or ' disabled',
                    logarange == "auto" and ' selected' or '',
                    logarange == "min" and ' selected' or '',
                    logarange == "tiny" and ' selected' or '',
                    logarange == "med" and ' selected' or '',
                    logarange == "lar" and ' selected' or '',
                    logarange == "max" and ' selected' or '',
                )


        print '<HR>'

        tranges = {
                7200: 'Two hours',
                43200: 'Twelve hours',
                86400: 'One day',
                604800: 'One week',
                2592000: 'One month',
                31622400: 'One year',
            }

        trkeys = tranges.keys()
        trkeys.sort()

        for start in trkeys:
            #
            picname = '%s/%s_%s_%i.png' % (
                    picturepath,
                    targetDEVICE.hostname,
                    ifaceNameCleaned,
                    start
                )

            rrdb = '%s/%s/%s.rrd' % (
                    rrddir,
                    targetDEVICE.hostname,
                    ifaceNameCleaned
                )

            #
            # what to draw (bps, pps...):
            pic = tg_inc.drawPic(targetDEVICE, what, rrdb, picname,
                    start=-start, title=None, w=450, h=100,
                    loga=loga, logarange=logarange, cf=cf)

            if pic:
                print '<TR><TD colspan="2"><B>%s:</B><BR>' % (tranges[start])
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
""" % (targetdevice and
    '&bull; <a href="tg_status.py?device=%s">This device\'s health</a>' % targetDEVICE.hostname
        or '')

# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################

