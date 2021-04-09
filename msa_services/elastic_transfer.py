import uuid
import time
from hostlist import expand_hostlist, collect_hostlist
from elastic_observer import ci_now
from elastic_parameters import Parameters
from logzero import logger
from ms_utility import timing

@timing
def transfer_execute(hws, transfer_requests, clusters_loc, iteration):
    logger.info(f"-#- execute transfer begin {iteration} -#-")
    # submit request to source broker
    n_submitted=0
    for idx, r in enumerate(transfer_requests):
        if r['nnodes'] < 0:
            r['status']='discarded'
            continue
        res = hws.reservenodes(r['src'], r['nnodes'], r['node_type'])
        r['id']=res
        if res is None:
            r['status']='not_created'
        else:
            r['ts_start_request'] = ci_now(clusters_loc[r['src']])
            r['status']='to_proceed'
            n_submitted+=1
    if n_submitted == 0:
        return []
    logger.info(f"total submitted requests: {n_submitted}")

    # monitor submitted request and do the transfer when completed
    max_request_completion_time = Parameters.max_request_completion_time
    wait_iteration=Parameters.wait_iteration
    max_iteration=int(max_request_completion_time/wait_iteration)
    wait_iteration*=Parameters.clock_rate
    it=0
    n_completed = n_failed = 0
    while it < max_iteration and (n_completed + n_failed) < n_submitted:
        for r in transfer_requests:
            if r['status'] == 'to_proceed':
                status, nodelist, nnodes = hws.task(r['id'])
                if status == 'error':
                    n_failed+=1
                    r['status'] = 'error'
                    continue
                if status == 'completed':
                    if nnodes == r['nnodes']:
                        res = transfer_swap_nodes(hws, r, r['src'], r['dst'], nodelist, iteration)
                        r['ts_end_request'] = ci_now(clusters_loc[r['dst']])
                        if res:
                            r['status'] = 'completed'
                            r['nnodes_transferred'] = nnodes
                            n_completed+=1
                        else:
                            r['status'] = 'completed_failed'
                            n_failed+=1
        logger.info(f"check: it={it}, n_completed={n_completed}/{n_submitted}, n_failed={n_failed}")
        time.sleep(wait_iteration)
        it+=1

    # cancel requests
    n_cancel = n_cancel_failed = 0
    for r in transfer_requests:
        if r['status'] == 'to_proceed':
            res = hws.cancel(r['id'])
            if not res:
               r['status']='canceled_failed'
               n_cancel_failed+=1
            else:
               r['status']='canceled'
               n_cancel+=1
    logger.info(f"cancel: n_cancel={n_cancel}, n_cancel_failed={n_cancel_failed}")

    # proceed incomplete request with a nodelist
    n_partialy_completed = n_partialy_completed_failed = 0
    for r in transfer_requests:
        if r['status'] == 'canceled':
            status, nodelist, nnodes = hws.task(r['id'])
            if status == 'error' or nnodes == 0:
                continue
            res = transfer_swap_nodes(hws, r, r['src'], r['dst'], nodelist, iteration)
            r['ts_end_request'] = ci_now(clusters_loc[r['dst']])
            if res:
               r['status']='partially_completed'
               r['nnodes_transferred'] = nnodes
               n_partialy_completed+=1
            else:
               r['status']='partially_complete_failed'
               n_failed+=1
    logger.info(f"partialy complete: n_partialy_completed={n_partialy_completed}, n_partialy_completed_failed={n_partialy_completed_failed}")

    # terminate requests
    n_terminated = n_terminated_failed = 0
    for r in transfer_requests:
        if r['status'] != 'completed' and r['status'] != 'not_created' and r['status'] != 'discarded':
            res = hws.terminate(r['id'])
            if res is not None:
               r['terminated']='success'
               n_terminated+=1
            else:
               r['terminated']='failed'
               n_terminated_failed+=1
        else:
            r['terminated']='skipped'
    logger.info(f"terminate: n_terminated={n_terminated}, n_terminated_failed={n_terminated_failed}")
    logger.info(f"-#- execute transfer end {iteration} -#-")
    return transfer_requests

@timing
def transfer_swap_nodes(hws, request, src, dst, nodelist, iteration):
    task_id = request['id']
    if len(nodelist) > 0:
        res = hws.setnodes(dst, nodelist)
        if res is False:
            logger.error(f"-- importing node failed")
            return False
        extracted_node = hws.extractnodes(task_id)
        if extracted_node is None:
            logger.error(f"-- extract node failed")
            return False
    logger.info(f"-- transfer {src} -> {dst} completed.")
    return True

