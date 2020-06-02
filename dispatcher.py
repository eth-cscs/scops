import uuid
import time
from hostlist import expand_hostlist, collect_hostlist
from parameters import Parameters


class ScopsDispatcher:

    def __init__(self, clock_rate):
        self.clock_rate = clock_rate

    def cleanupIteration(self, clusters, requests):
        for r in requests:
           clusters[r['src']].cleanup(r)

    def getClustersUsage(self, clusters):
        usage=dict()
        for name in clusters:
            usage[name] = clusters[name].getJobsUsage()
        return usage

    def executeTransfers(self, transfer_requests, clusters, iteration):
        # submit request to source broker
        n_todo=0
        n_submitted_jobs=0
        for r in transfer_requests:
            if r['nnodes'] < 0:
                r['status']='discarded'
                continue
            res, njobs = clusters[r['src']].requestNodes(r)
            n_submitted_jobs+=njobs
            if res < 0:
                r['status']='not_created'
            else:
                r['status']='to_proceed'
                n_todo+=1
        if n_todo == 0:
            return []
        print("[DI%d] total submitted jobs for transfer: %d" % (iteration, n_submitted_jobs))

        # monitor submitted request and do the transfer when completed
        max_request_completion_time=Parameters.max_request_completion_time
        wait_iteration=Parameters.wait_iteration
        max_iteration=int(max_request_completion_time/wait_iteration)
        wait_iteration*=self.clock_rate
        it=0
        n_completed = n_failed = 0
        while it < max_iteration and (n_completed + n_failed) < n_todo:
            for i, r in enumerate(transfer_requests):
                if r['status'] == 'to_proceed':
                    new_req = clusters[r['src']].checkRequests(r)
                    if new_req != -1:
                        transfer_requests[i] = r = new_req
                        if len(expand_hostlist(r['nodelist'])) == r['nnodes']:
                            res = self.transferNodes(r, clusters, iteration)
                            if res < 0:
                                r['status']='completed_failed'
                                n_failed+=1
                            else:
                                r['status']='completed'
                                n_completed+=1
            print("[DI%d] it=%d, n_completed=%d/%d, n_failed=%d" % (iteration, it, n_completed, n_todo, n_failed))
            time.sleep(wait_iteration)
            it+=1

        # cancel requests
        reasons=list()
        n_cancel = n_cancel_failed = 0
        max_cancel_wait_time=0
        for r in transfer_requests:
            if r['status'] == 'to_proceed':
                res = clusters[r['src']].cancelRequests(r)
                if res < 0:
                   r['status']='canceled_failed'
                   n_cancel_failed+=1
                else:
                   r['status']='canceled'
                   n_cancel+=1
                   reasons+=list(r['reason'])
                   r_wait=r['ts_cancel']-r['ts_request']
                   if r_wait > max_cancel_wait_time:
                       max_cancel_wait_time = r_wait
        print("[DI%d] n_cancel=%d, n_cancel_failed=%d, reasons for cancel='%s', max_cancel_wait_time=%d" % (iteration, n_cancel, n_cancel_failed, str(set(reasons)), max_cancel_wait_time))

        # proceed incomplete request with a nodelist
        n_partialy_completed = n_partialy_completed_failed = 0
        for r in transfer_requests:
            if r['status'] == 'canceled' and r['nodelist'] != '':
                res = self.transferNodes(r, clusters, iteration)
                if res < 0:
                   r['status']='partially_complete_failed'
                   n_failed+=1
                else:
                   r['status']='partially_completed'
                   n_partialy_completed+=1
        print("[DI%d] n_partialy_completed=%d, n_partialy_completed_failed=%d" % (iteration, n_partialy_completed, n_partialy_completed_failed))

        # terminate requests
        n_terminated = n_terminated_failed = 0
        for r in transfer_requests:
            if r['status'] != 'completed' and r['status'] != 'not_created' and r['status'] != 'discarded':
                res = clusters[r['src']].terminateRequests(r)
                if res < 0:
                   r['terminated']='failed'
                   n_terminated_failed+=1
                else:
                   r['terminated']='success'
                   n_terminated+=1
            else:
                r['terminated']='skipped'
                r['ts_terminated']=r['ts_transfer']
        print("[DI%d] n_terminated=%d, n_terminated_failed=%d" % (iteration, n_terminated, n_terminated_failed))
        return transfer_requests

    def transferNodes(self, request, clusters, iteration):
        res = clusters[request['dst']].addNodes(request)
        if res < 0:
            print('[DI%d] Importing node failed' % (iteration))
            return res
        request['ts_transfer']=request['ts_addnodes']
        res = clusters[request['src']].removeNodes(request)
        if res < 0:
            print('[DI%d] Exporting node failed' % (iteration))
            return res
        request['ts_transfer']=request['ts_removenodes']
        return 0

