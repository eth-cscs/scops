from remoteexec import remote_execute
from hostlist import expand_hostlist, collect_hostlist
import time
import re


class SlurmResourceBroker:

    def __init__(self):
        pass

    def setNodesState(self, location, nodelist, state):
        command = "scontrol update NodeName=%s state=%s Reason='scops elasticity'" % (nodelist, state)
        output = remote_execute(location, command)
        if output != "" or output is None:
            print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
            return -1
        return 0

    def removeNodesFromRsv(self, location, request):
        res = self.setNodesState(location, request['nodelist'], "DOWN")
        if res < 0:
            return res
        command = "rsvmgt scops-%d-%s - %s" % (request['iteration'], request['id'], request['nodelist'])
        output = remote_execute(location, command)
        if (output != "" and output != "Reservation updated.") or output is None:
            print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
            return -1
        request['nnodes']-=len(expand_hostlist(request['nodelist']))
        request['nodelist']=''
        return request

    def executeRequests(self, location, request):
        # find number of job to submits
        if request['nnodes'] > 20:
            nnodes=int(request['nnodes']/10)
            ntimes=int(request['nnodes']/nnodes)
            remain_nodes=request['nnodes']-nnodes*ntimes
        else:
            nnodes=request['nnodes']
            ntimes=1
            remain_nodes=0
        job_name="scops-%d-%s" % (request['iteration'], request['id'])
        command = "relocate %s %d %s %d" % (request['node_type'], nnodes, job_name, ntimes)
        output = remote_execute(location, command)
        if output == "" or output is None:
            print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
            return -1, 0
        if remain_nodes > 0:
            command = "relocate %s %d %s %d" % (request['node_type'], remain_nodes, job_name, 1)
            output = remote_execute(location, command)
            if output == "" or output is None:
               print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
               return -1, 0
            ntimes+=1
        return 0, ntimes

    def cancelRequests(self, location, request):
        # get reason
        command = "squeue -h --state=PD --name=scops-%d-%s -o '%%r'" % (request['iteration'], request['id'])
        output = remote_execute(location, command)
        if output == "" or output is None:
           request['reason']=set(['Unknown'])
        else:
           splitted_output = re.split('\n', output)
           request['reason']=set(splitted_output)

        # cancel jobs
        command = "scancel --name scops-%d-%s" % (request['iteration'], request['id'])
        output = remote_execute(location, command)
        if output != "" or output is None:
           print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
           return -1
        return 0

    def terminateRequests(self, location, request):
        # remove reservation
        command = "rsvmgt scops-%d-%s rm" % (request['iteration'], request['id'])
        output = remote_execute(location, command)
        if output != "" or output is None:
           print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
           return -1
        return 0

    def cleanup(self, location, request):
        command = "cleanup scops-%d-%s" % (request['iteration'], request['id'])
        output = remote_execute(location, command)
        if output != "" or output is None:
           print("[CL%d] cleaning %s, output: '%s'" % (request['iteration'], request['src'], output))
           return -1
        return 0

    def checkNodesOfRequest(self, location, request):
        command = "rsvnodelist scops-%d-%s" % (request['iteration'], request['id'])
        output = remote_execute(location, command)
        if output == "" or output is None:
           print("[!!ERROR-BR!!] Command : %s\nOutput: '%s'" % (command, output))
           return -1
        if output.startswith('No nodelist') or output.startswith('No reservation'):
            return request
        splitted_output = re.split('\n',output)
        resources=list()
        for t in splitted_output:
            node_type, nodelist = t.split(' ')
            if request['node_type'] in node_type.split(','): # should always be true
                resources+=expand_hostlist(nodelist)
        request['nodelist']=collect_hostlist(resources)
        return request
