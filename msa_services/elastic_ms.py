from datetime import datetime
import time
import json
import argparse
from logzero import logger, logfile

from elastic_transfer import transfer_execute
from elastic_observer import ci_now, ci_current_load
from elastic_arbiter import arb_resource_allocation
from elastic_parameters import Parameters
from elastic_utility import append_usage, append_request, print_usage, append_divclock
from registry_intf import Registry
from hwstate_mgr_intf import HWState_mgr

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# global system definition
global_node_types=['gpu', 'mc']
hpc_cap={'gpu': 5688, 'mc': 1630}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--registry", action="store", default="register:12000")
    parser.add_argument("-w", "--hws", action="store")
    parser.add_argument("-c", "--ci_configdir", action="store", default="/ci_config")
    parser.add_argument("-l", "--ci_list", action="store", required=True)
    args = parser.parse_args()

    ci_configdir = args.ci_configdir
    ci_list = args.ci_list.split(',')

    registry = Registry(args.registry)
    if args.hws is not None:
        hws_location = args.hws
    else:
        hws_location = registry.locate('hwstate_mgr')
        if hws_location is None:
            hws_location = 'hwstate_mgr:12010'
            logger.info(f"Use default location for hwstate_mgr: {hws_location}")
    hws = HWState_mgr(hws_location)

    logfile("/data/elastic_ms.log")

    # define cluster instances
    clusters = dict()
    for ci_name in ci_list:
        with open(f"{ci_configdir}/{ci_name}.json") as f:
            clusters[ci_name] = json.load(f)
    logger.info(f"Loaded {len(clusters)} cluster instances: {','.join(clusters.keys())}")

    attempt = 100
    service_list = registry.list()
    while (service_list is None or 'ci' not in service_list or len(service_list['ci']) < len(clusters)) and attempt > 0:
        time.sleep(15)
        service_list = registry.list()
        attempt-=1
    if attempt == 0:
        logger.error("No cluster instances found.")
        exit(0)

    clusters_loc = dict() # helper
    for ci_name in clusters:
        clusters[ci_name]['location'] = service_list['ci'][ci_name]
        clusters_loc[ci_name] = service_list['ci'][ci_name]
    logger.info(f"Located {len(clusters)} cluster instances: {','.join(clusters.keys())}")

    #clusters_loc['ce_uzh']='0.0.0.0:17101'
    #clusters_loc['pt_eth']='0.0.0.0:17201'

    clock_rate=Parameters.clock_rate
    iteration_elaspedTime=int(Parameters.iteration_elaspedTime*clock_rate)

    iteration=0
    # main loop
    while True:
        logger.info(f"[IT{iteration}] elastic iteration={iteration}")
        ts = time.time()
        ts_all = time.time()

        # cluster instance time divergence
        div_now=dict()
        for k in clusters:
            div_now[k]=ci_now(clusters_loc[k])
        if len([x for x in div_now.values() if x > 0]) > 0:
           min_v = min([x for x in div_now.values() if x > 0])
           min_c = [k for k, v in div_now.items() if v==min_v]
           max_v = max([x for x in div_now.values()])
           max_c = [k for k, v in div_now.items() if v==max_v]
           div_global_now = {'iteration': iteration, 'min_c': min_c, 'min_v': min_v,
                                                     'max_c': max_c, 'max_v': max_v}
           append_divclock(div_global_now)
           logger.info(f"[IT{iteration}] - [{datetime.fromtimestamp(min_v)}] Clock div: {max_v-min_v} max clusters: {max_c}, min clusters: {min_c}")
        else:
            if iteration == 0:
               continue

        # identify clusters' load
        ci_load=dict()
        for k in clusters:
            ci_load[k] = ci_current_load(clusters_loc[k], clusters[k]['node_types'])
        print_usage(ci_load, iteration)
        append_usage(div_now, iteration, ci_load)

        # check if capacity is correct?
        # false positive if observer cannot get data
        # false positive if drain nodes are set
        check_cap={ 'gpu': 0, 'mc': 0}
        for name in ci_load.keys():
            if 'node_types' in ci_load[name]:
                for n in ci_load[name]['node_types']:
                    if 'cap' in ci_load[name][n]:
                        check_cap[n]+=ci_load[name][n]['cap']
        for n in global_node_types:
            if check_cap[n] != hpc_cap[n]:
                logger.warning(f"[IT{iteration}] {n} capacity different {check_cap[n]} != {hpc_cap[n]}")

        # resource allocation
        transfer_requests = arb_resource_allocation(ci_load, clusters, global_node_types, iteration, hpc_cap)
        total_requested_nodes={'gpu': 0, 'mc': 0}
        logger.info(f"[IT{iteration}] Transfer requests")
        for k in transfer_requests:
            logger.info(f"[IT{iteration}] [TR] {k['src']}->{k['dst']} {k['nnodes']}{k['node_type']} {k['algo']}")
            total_requested_nodes[k['node_type']]+=k['nnodes']

        # execute resource transfer
        executed_requests = transfer_execute(hws, transfer_requests, clusters_loc, iteration)
        append_request(div_now, executed_requests)
        logger.info(f"[IT{iteration}] Executed requests:")
        total_transferred_nodes={'gpu': 0, 'mc': 0}
        for k in executed_requests:
            logger.info(f"[IT{iteration}] [ER] {k['src']} -> {k['dst']} {k['node_type']}:{k['nnodes']} {k['status']} {k['id']}")
            total_transferred_nodes[k['node_type']]+=k['nnodes_transferred']
        for n in global_node_types:
            if total_requested_nodes[n] > 0:
                logger.info(f"[IT{iteration}] {n} requested_nodes={total_requested_nodes[n]}, transferred_nodes={total_transferred_nodes[n]}")

        # wait next iteration
        te = time.time()
        wait_nextIteration = round(iteration_elaspedTime - (te - ts),0)
        if wait_nextIteration > 0:
           logger.info(f"[IT{iteration}] Wait next iteration {wait_nextIteration} real seconds")
           for k in range(0,Parameters.n_pokes):
               ts = time.time()
               for k in clusters:
                   div_now[k]=ci_now(clusters_loc[k])
                   ci_load[k] = ci_current_load(clusters_loc[k], clusters[k]['node_types'])
               append_usage(div_now, iteration, ci_load)
               te = time.time()
               poke_wait = round(int(wait_nextIteration/Parameters.n_pokes) - (te - ts),0)
               if poke_wait > 0:
                  logger.info(f"[IT{iteration}] next poke in {poke_wait} real seconds")
                  time.sleep(poke_wait)
        # final cleanup just in case
        for r in executed_requests:
            hws.terminate(r['id'])
        te_all = time.time()
        logger.info(f"[IT{iteration}] Iteration lasted {round(te_all-ts_all,1)} real seconds")
        iteration+=1

### For scenario 2, after X iterations create a dummy cluster with no location, observer and broker.
### Just make the predicate return True and a high priority
