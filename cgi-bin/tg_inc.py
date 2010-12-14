#
#

import os
import sys

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


def drawPic_LC(picname, rrdfile,
        start=-86400, end='now', title=None, w=450, h=100, what='bps',
        loga=False, logarange="auto", cf="avg"):
    """Returns path to pic or None."""
    #
    CFs = {
        'avg': 'AVERAGE',
        'max': 'MAX',
    }
    CF = CFs[cf]

    # common:
    graphargs = [
                picname,
                '-s %i' % start,
                '-e %s' % str(end),
                '-v %s' % what,
                '-w %i' % w,
                '-h %i' % h,
                #'--right-axis 0.001:0',
                #'--right-axis-format %1.1lf',
                #"--right-axis-label 'Mplts/sec'",
                # '-A',
                # '-Y',
        ]

    #
    # log scale:
    if loga:
        loga_opts = {
            'min': [ '-o', '-l 0.01', '-u 1', '-r' ],
            'tiny': [ '-o', '-l 0.1', '-u 10', '-r' ],
            'med': [ '-o', '-l 1', '-u 100', '-r' ],
            'lar': [ '-o', '-l 10', '-u 1000', '-r' ],
            'max': [ '-o', '-l 100', '-u 10000', '-r' ],
        }
        graphargs.extend(loga_opts.get(logarange, ['-o']))
    else:
        graphargs.append('-l 0')

    #
    # if title:
    if title:
        graphargs.append('-t %s' % title)
    #
    # defs:
    addit_graphargs = {
        'bps': [ 'DEF:inbytes=%s:in_bytes:%s' % (rrdfile, CF),
                 'CDEF:inbits=inbytes,8,*',
                 'DEF:outbytes=%s:out_bytes:%s' % (rrdfile, CF),
                 'CDEF:outbits=outbytes,8,*',
                 'AREA:inbits#55CC55:In',
                 'LINE2:outbits#5555CC:Out'
               ],
        'pps': [ 'DEF:inupkts=%s:in_upkts:%s' % (rrdfile, CF),
                 'DEF:outupkts=%s:out_upkts:%s' % (rrdfile, CF),
                 'DEF:innupkts=%s:in_nupkts:%s' % (rrdfile, CF),
                 'DEF:outnupkts=%s:out_nupkts:%s' % (rrdfile, CF),
                 'LINE1:inupkts#55CC55:Ucast In',
                 'LINE1:outupkts#5555CC:Ucast Out',
                 'LINE1:innupkts#CC5555:Bcast In',
                 'LINE1:outnupkts#333333:Bcast Out',
               ],
        'bpp': [ # bytes:
                 'DEF:inbytes=%s:in_bytes:%s' % (rrdfile, CF),
                 'DEF:outbytes=%s:out_bytes:%s' % (rrdfile, CF),
                 ## bits:
                 #'CDEF:inbits=inbytes,8,*',
                 #'CDEF:outbits=outbytes,8,*',
                 #
                 # packets:
                 'DEF:inupkts=%s:in_upkts:%s' % (rrdfile, CF),
                 'DEF:outupkts=%s:out_upkts:%s' % (rrdfile, CF),
                 'DEF:innupkts=%s:in_nupkts:%s' % (rrdfile, CF),
                 'DEF:outnupkts=%s:out_nupkts:%s' % (rrdfile, CF),
                 # totpacks -- ucast + bcast:
                 # if [in,out]bpkts == U, set it to zero:
                 'CDEF:intotpacks=inupkts,innupkts,UN,0,innupkts,IF,+',
                 'CDEF:outtotpacks=outupkts,outnupkts,UN,0,outnupkts,IF,+',
                 #
                 # bpp -- bits per packet:
                 'CDEF:inbpp=inbytes,intotpacks,/',
                 'CDEF:outbpp=outbytes,outtotpacks,/',
                 #
                 'LINE1:inbpp#55CC55:BPP In',
                 'LINE1:outbpp#5555CC:BPP Out',
               ],
    }

    graphargs.extend(addit_graphargs.get(what, ['']))

    try:
        rrdtool.graph(*graphargs)
    except Exception, why:
        print 'Exception: %s<BR>' %why
        return None

    return picname

def drawPic_HC(picname, rrdfile,
        start=-86400, end='now', title=None, w=450, h=100, what='bps',
        loga=False, logarange="auto", cf="avg"):
    """Returns path to pic or None."""
    #
    CFs = {
        'avg': 'AVERAGE',
        'max': 'MAX',
    }
    CF = CFs[cf]

    # common:
    graphargs = [
                picname,
                '-s %i' % start,
                '-e %s' % str(end),
                '-v %s' % what,
                '-w %i' % w,
                '-h %i' % h,
                #'--right-axis 0.001:0',
                #'--right-axis-format %1.1lf',
                #"--right-axis-label 'Mplts/sec'",
                # '-A',
                # '-Y',
        ]

    #
    # log scale:
    if loga:
        loga_opts = {
            'min': [ '-o', '-l 0.01', '-u 1', '-r' ],
            'tiny': [ '-o', '-l 0.1', '-u 10', '-r' ],
            'med': [ '-o', '-l 1', '-u 100', '-r' ],
            'lar': [ '-o', '-l 10', '-u 1000', '-r' ],
            'max': [ '-o', '-l 100', '-u 10000', '-r' ],
        }
        graphargs.extend(loga_opts.get(logarange, ['-o']))
    else:
        graphargs.append('-l 0')

    #
    # if title:
    if title:
        graphargs.append('-t %s' % title)
    #
    # defs:
    addit_graphargs = {
        'bps': [ 'DEF:inbytes=%s:in_bytes:%s' % (rrdfile, CF),
                 'CDEF:inbits=inbytes,8,*',
                 'DEF:outbytes=%s:out_bytes:%s' % (rrdfile, CF),
                 'CDEF:outbits=outbytes,8,*',
                 'AREA:inbits#55CC55:In',
                 'LINE2:outbits#5555CC:Out'
               ],
        'pps': [ 'DEF:inupkts=%s:in_upkts:%s' % (rrdfile, CF),
                 'DEF:outupkts=%s:out_upkts:%s' % (rrdfile, CF),
                 'DEF:inbpkts=%s:in_bpkts:%s' % (rrdfile, CF),
                 'DEF:outbpkts=%s:out_bpkts:%s' % (rrdfile, CF),
                 'DEF:inmpkts=%s:in_mpkts:%s' % (rrdfile, CF),
                 'DEF:outmpkts=%s:out_mpkts:%s' % (rrdfile, CF),
                 'CDEF:neg_inupkts=0,inupkts,-',
                 'CDEF:neg_outupkts=0,outupkts,-',
                 'CDEF:neg_inmpkts=0,inmpkts,-',
                 'CDEF:neg_outmpkts=0,outmpkts,-',
                 # 'CDEF:non_ucasts_in=0,inbpkts,-,inmpkts,-,1,*',
                 # 'AREA:inupkts#7B68EE28:Ucast In',
                 # 'AREA:inbpkts#00FA9A98:Bcast In',
                 # 'AREA:inmpkts#FFDAB998:Mcast In',
                 'AREA:outupkts#80808028:U-out',
                 'AREA:outbpkts#FFFF006F:B-out',
                 'AREA:outmpkts#0000FF1F:M-out',
                 # 'LINE2:outmpkts#7FFFD4:Mcast Out',
                 'LINE1:inupkts#0000CD:U-in',
                 'LINE2:inbpkts#228B22:B-in',
                 'LINE1:inmpkts#FF0000:M-in',
                 # 'LINE1:non_ucasts_in#FF0000:NU-in',
               ],
        'bpp': [ # bytes:
                 'DEF:inbytes=%s:in_bytes:%s' % (rrdfile, CF),
                 'DEF:outbytes=%s:out_bytes:%s' % (rrdfile, CF),
                 ## bits:
                 #'CDEF:inbits=inbytes,8,*',
                 #'CDEF:outbits=outbytes,8,*',
                 #
                 # packets:
                 'DEF:inupkts=%s:in_upkts:%s' % (rrdfile, CF),
                 'DEF:outupkts=%s:out_upkts:%s' % (rrdfile, CF),
                 'DEF:inbpkts=%s:in_bpkts:%s' % (rrdfile, CF),
                 'DEF:outbpkts=%s:out_bpkts:%s' % (rrdfile, CF),
                 'DEF:inmpkts=%s:in_mpkts:%s' % (rrdfile, CF),
                 'DEF:outmpkts=%s:out_mpkts:%s' % (rrdfile, CF),
                 # totpacks -- ucast + bcast:
                 # if [in,out]bpkts == U, set it to zero:
                 'CDEF:intotpacks=inupkts,UN,0,inupkts,IF,inbpkts,UN,0,inbpkts,IF,inmpkts,UN,0,inmpkts,IF,+,+',
                 'CDEF:outtotpacks=outupkts,UN,0,outupkts,IF,outbpkts,UN,0,outbpkts,IF,outmpkts,UN,0,outmpkts,IF,+,+',
                 #
                 # bpp -- bits per packet:
                 'CDEF:inbpp=inbytes,intotpacks,/',
                 'CDEF:outbpp=outbytes,outtotpacks,/',
                 #
                 'LINE1:inbpp#55CC55:BPP In',
                 'LINE1:outbpp#5555CC:BPP Out',
               ],
    }

    graphargs.extend(addit_graphargs.get(what, ['']))

    try:
        rrdtool.graph(*graphargs)
    except Exception, why:
        print 'Exception: %s<BR>' %why
        return None

    return picname


drawPic = {
    'True': drawPic_HC,
    'False': drawPic_LC,
}


# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
