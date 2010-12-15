#
#
#


import snmpAgent

class Oid(snmpAgent.oid):
    def __init__(self, name, value, alias=None,
            rrdDST=None, rrdMin=0, rrdMax=4250000000):
        snmpAgent.oid.__init__(self, name, value, alias)
        self.rrdDST = rrdDST
        self.rrdMin = rrdMin
        self.rrdMax = rrdMax


class oidSets(dict):
    #def __init__(self):
    #    dict.__init__(self)

    def addToSet(self, setname, oid):
        targetSet = self.get(setname, "not found")
        if targetSet != "not found":
            if oid in targetSet:
                # print "Oid already in set %s" % setname
                # raise RuntimeError
                pass
            else:
                targetSet.append(oid)
        else:
            self.createSet(setname)
            self.addToSet(setname, oid)

    def createSet(self, setname):
        self[setname] = []


class oidManager(dict):
    def __init__(self):
        dict.__init__(self)
        # self.sets = dict()
        self.sets = oidSets()

    def newOid(self, name, oidtuple, alias, memberof=[],
            rrdDST=None, rrdMin=0, rrdMax=4250000000):
        if self.get(alias):
            # print "This alias is already in use."
            # raise RuntimeError
            pass

        #for a, o in self.items():
        #    if o.name == name:
        #        print "This name is already in use."
        #        raise RuntimeError

        # oid = snmpAgent.oid(name, oidtuple, alias)
        oid = Oid(name, oidtuple, alias, rrdDST, rrdMin, rrdMax)
        self[alias] = oid

        # TODO:
        for m in memberof:
            self.sets.addToSet(m, oid)

        return oid

    def getOidByAlias(self, alias):
        return self[alias]

    def getOidByName(self, name):
        for a, o in self.items():
            if o.name == name:
                return o
        else:
            return None

# oidmgr = oidManager()

#
# vim: expandtab ts=4 tabstop=4 shiftwidth=4 softtabstop=4:
######################
