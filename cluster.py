
class Cluster:

    def __init__(self, location, priority_w, share, predicate, predicate_values, node_types, observer, broker):
        self.location = location
        self.priority_w = priority_w
        self.share = share
        self.predicate = predicate
        self.predicate_values = predicate_values
        self.node_types = node_types
        self.observer = observer
        self.broker = broker

    def evalPredicate(self, usage, n):
        now = self.now()
        return self.predicate(usage, n, now, self.predicate_values)
#
# Observer wrapper and utilities
#
    def now(self):
        return self.observer.getSystemClock(self.location)

    def getJobsUsage(self):
        return self.observer.getJobsUsage(self.location, self.node_types)

#
# broker wrapper and utilities
#
    def cleanup(self, request):
        self.broker.cleanup(self.location, request)

    def addNodes(self, request):
        request['ts_addnodes']=self.now()
        nodelist = request['nodelist']
        if len(nodelist) > 0:
            # POWER_DOWN is better then RESUME, also it is unexpected
            # a state DOWN+DRAIN will become IDLE+DRAIN instead of IDLE with RESUME
            #return self.broker.setNodesState(self.location, nodelist, "POWER_DOWN")
            return self.broker.setNodesState(self.location, nodelist, "RESUME")
        else:
            return 0

    def removeNodes(self, request):
        request['ts_removenodes']=self.now()
        return self.broker.removeNodesFromRsv(self.location, request)

    def requestNodes(self, request):
        request['ts_request']=self.now()
        return self.broker.executeRequests(self.location, request)

    def terminateRequests(self, request):
        request['ts_terminate']=self.now()
        return self.broker.terminateRequests(self.location, request)

    def cancelRequests(self, request):
        request['ts_cancel']=self.now()
        return self.broker.cancelRequests(self.location, request)

    def checkRequests(self, request):
        request['ts_check']=self.now()
        return self.broker.checkNodesOfRequest(self.location, request)

