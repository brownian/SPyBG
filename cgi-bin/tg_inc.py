#
#

import os
import sys

import cgi
import cgitb; cgitb.enable()

import itertools

import ConfigParser

import rrdtool

from spybg import commonFuncs

colordefs = [
    '000000',
    'aa0000',
    'aa0000',
    '00aa00',
    '0000aa',
]

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


def drawPic(device, what, rrdb, picname,
        start=-86400, end='now', title=None, w=450, h=100,
        loga=False, logarange="auto", cf="avg"):
    """Returns path to pic or None."""
    #
    CFs = {
        'avg': 'AVERAGE',
        'max': 'MAX',
    }
    CF = CFs[cf]

    colorspool = itertools.cycle(colordefs)

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

    # graphargs.extend(addit_graphargs.get(what, ['']))
    graphargs.extend([
            'DEF:%s=%s:%s:%s' % (vname, rrdb, vname, CF)
                for vname in device.subsets[what]
        ])

    # 'LINE1:outbpp#5555CC:BPP Out',
    graphargs.extend([
            'LINE1:%s#%s:%s' % (vname, colorspool.next(), vname)
                for vname in device.subsets[what]
        ])

    # print graphargs


    try:
        rrdtool.graph(*graphargs)
    except Exception, why:
        print 'Exception: %s<BR>' %why
        return None

    return picname


# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
