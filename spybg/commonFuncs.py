#
#
#

def timedelta2secs(tdelta):
    return tdelta.seconds + (tdelta.microseconds+.0)/1000000


def checkConfig(dir):
    if not (os.access(dir, os.F_OK) and os.access(dir, os.W_OK)):
        # should go to log?..
        print 'Error: %s is not exists or not writable.' % dir

        return False

    else:
        return True


def cleanHostdirName(hostdir):
    hostdir = hostdir.replace('#', 'No')
    hostdir = hostdir.replace('@', 'at')
    hostdir = hostdir.replace(' ', '_')
    return hostdir

def cleanIfName(name):
    name = name.replace(' ', '_')
    name = name.replace('/', '_')
    name = name.replace(':', '_')
    return name


def sortOids(o1, o2):
    """Sorts oids by alias."""
    return cmp(o1.alias, o2.alias)

def sortStrNum(s1, s2):
    """Sorts strings numerically."""
    return cmp(int(s1), int(s2))

#
# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################

