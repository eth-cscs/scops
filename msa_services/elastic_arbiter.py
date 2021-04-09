import numpy as np
import networkx as nx
from elastic_parameters import Parameters
from logzero import logger
from ms_utility import timing
import elastic_predicate

def arb_knapsack_dp(values,weights,n_items,capacity):
    table = np.zeros((n_items+1,capacity+1),dtype=np.float32)
    keep = np.zeros((n_items+1,capacity+1),dtype=np.float32)
    for i in range(1,n_items+1):
        for w in range(0,capacity+1):
            wi = weights[i-1] # weight of current item
            vi = values[i-1] # value of current item
            if (wi <= w) and (vi + table[i-1,w-wi] > table[i-1,w]):
                table[i,w] = vi + table[i-1,w-wi]
                keep[i,w] = 1
            else:
                table[i,w] = table[i-1,w]
    picks = []
    K = capacity
    for i in range(n_items,0,-1):
        if keep[i,K] == 1:
            picks.append(i)
            K -= weights[i-1]
    picks.sort()
    picks = [x-1 for x in picks] # change to 0-index
    max_val = table[n_items,capacity]
    return picks,max_val

def arb_cleanupRequestsOffers(requests, offers, nodetype):
    # clean up same name in offers
    for i in range(0, len(offers)):
        for j in range(i+1, len(offers)):
            if offers[i][0] == offers[j][0]:
                #print("Cleaning-up offers:",nodetype,offers[i],offers[j])
                max_offer = max(offers[i][1], offers[j][1])
                if offers[i][1] == max_offer:
                   offers[j][1]=0
                else:
                   offers[i][1]=0
    # clean up same name in requests
    for i in range(0, len(requests)):
        for j in range(i+1, len(requests)):
            if requests[i][0] == requests[j][0]:
                #print("Cleaning-up /!!!\\ requests:",nodetype,requests[i],requests[j])
                max_offer = max(requests[i][1], requests[j][1])
                if requests[i][1] == max_offer:
                   requests[j][1]=0
                else:
                   requests[i][1]=0
    # clean up same name in requests and offers
    for r in requests:
        for o in offers:
            if r[0] == o[0]:
                #print("Cleaning-up requests/offers:",nodetype,r,o)
                if r[1] > o[1]:
                    r[1]-=o[1]
                    o[1]=0
                else:
                    o[1]-=r[1]
                    r[1]=0
                    break
    return [ r for r in requests if r[1] > 0], [ o for o in offers if o[1] > 0]

def arb_create_transfer_requests(requests, offers, nodetype, transfer_requests, algo, iteration):
    idx_o = 0
    idx_r = 0
    s_requests = sorted([ r for r in requests if r[1] > 0], key=lambda tup: tup[1])
    s_offers = sorted([o for o in offers if o[1] > 0], key=lambda tup: tup[1])
    while idx_r < len(s_requests) and idx_o < len(s_offers):
        name_o, nodes_o = s_offers[idx_o]
        name_r, nodes_r = s_requests[idx_r]
        if nodes_o <= nodes_r:
            s_requests[idx_r][1] -= nodes_o
            s_offers[idx_o][1] = 0
            req={ 'nnodes': nodes_o, 'nnodes_transferred': 0, 'nodelist':'', 'node_type': nodetype, 'id': None, 'src': name_o, 'dst': name_r, 'status': 'created', 'algo': algo, 'iteration': iteration, 'ts_start_request': -1, 'ts_end_request': -1}
            transfer_requests.append(req)
            idx_o+=1
            if s_requests[idx_r][1] == 0:
                idx_r+=1
        else:
            s_offers[idx_o][1] -= nodes_r
            req={ 'nnodes': nodes_r, 'nnodes_transferred': 0, 'nodelist':'', 'node_type': nodetype, 'id': None, 'src': name_o, 'dst': name_r, 'status': 'created', 'algo': algo, 'iteration':iteration, 'ts_start_request': -1, 'ts_end_request': -1}
            transfer_requests.append(req)
            s_requests[idx_r][1] = 0
            idx_r+=1
    return s_requests, s_offers, transfer_requests

def arb_factorize_tranfer_requests(transfer_requests, node_types):
    f_transfer_requests=transfer_requests
    for n in node_types:
        all_found=False
        while not all_found:
            G=nx.DiGraph()
            for r in f_transfer_requests:
                if n == r['node_type']:
                   G.add_edge(r['src'], r['dst'])
            cycles = list(nx.simple_cycles(G))
            if len(cycles) == 0:
                all_found=True
                break
            c = cycles[0]
            c.append(c[0])
            print("cycle:",c)
            idx = 0
            cycle_requests=list()
            while idx < len(c)-1:
                src=c[idx]
                dst=c[idx+1]
                for r in f_transfer_requests:
                    if r['src'] == src and r['dst'] == dst and r['node_type'] == n:
                        cycle_requests.append(r)
                        break
                idx+=1
            print(cycle_requests)
            min_r = min(cycle_requests, key=lambda x:x['nnodes'])
            min_nodes=min_r['nnodes']
            print("min_r:",min_r)
            for rc in cycle_requests:
                for r in f_transfer_requests:
                    if rc['id'] == r['id']:
                        r['nnodes']-=min_nodes
                        break
            f_transfer_requests = [ k for k in f_transfer_requests if k['nnodes'] > 0 ]
    return f_transfer_requests

def arb_eval_predicate(clusters, name, active_c_n, n):
    pred = getattr(elastic_predicate, clusters[name]['model']['pred'])
    pred_value = clusters[name]['model']['pred_value']
    return pred(active_c_n, n, pred_value)

@timing
def arb_resource_allocation(usage, clusters, global_node_types, iteration, hpc_cap):
    logger.info(f"-#- resource allocation begin {iteration} -#-")
    # group and setup data
    active_clusters=[name for name in usage.keys() if usage[name]['status'] == 'success']
    pending_loaded_clusters=dict()
    total_offer=dict()
    offers=dict()
    requests=dict()
    for n in global_node_types:
        total_offer[n]=0
        offers[n]=list()
        requests[n]=list()
        pending_loaded_clusters[n]=list()
    for name in active_clusters:
        for n in clusters[name]['node_types']:
            if 'pending' in usage[name][n] and usage[name][n]['pending'] > 0:
                pending_loaded_clusters[n].append(name)

    # TODO this part can be removed, we could use active_cluster in the predicate section
    # generate offers of all active clusters without pending load
    for name in active_clusters:
        for n in usage[name]['node_types']:
            if name not in pending_loaded_clusters[n]:
                cap_cluster=0
                if 'cap' in usage[name][n]:
                    cap_cluster = usage[name][n]['cap']
                if 'running' in usage[name][n]:
                    cap_cluster-=usage[name][n]['running']
                if cap_cluster > 0:
                    total_offer[n] += cap_cluster
                    offers[n].append([name, cap_cluster])
    for n in global_node_types:
        if len(offers[n]) > 0:
            logger.info(f"offers of clusters without a workload: {n} {offers[n]}")

    # generate offers/requests of loaded clusters depending on predicate
    pred_values=dict()
    for n in global_node_types:
        pred_values[n]=dict()
        for name in pending_loaded_clusters[n]:
            active_c_n = usage[name][n]
            # test predicate
            if arb_eval_predicate(clusters, name, active_c_n, n):
                # offers
                pred_values[n][name]=True
                max_jobsize = active_c_n['max_pending']
                cap_cluster = active_c_n['cap']
                running = active_c_n['running']
                offer = cap_cluster - running - max_jobsize
                if offer > 0:
                   total_offer[n] += offer
                   offers[n].append([name, offer])
                else:
                   offer = int(cap_cluster*Parameters.omega)
                   if offer > 0:
                      total_offer[n] += offer
                      offers[n].append([name, offer])
            else:
                # requests
                pred_values[n][name]=False
                max_jobsize = active_c_n['max_pending']
                cap_cluster = active_c_n['cap']
                load_cluster = active_c_n['pending']
                running = active_c_n['running']
                require = max_jobsize - (cap_cluster - running)
                if  require > 0:
                   requests[n].append([name, require])
                else:
                   require = int(load_cluster*Parameters.rho)
                   if require > 0:
                      requests[n].append([name, require])
    # cap requests to maximum offer
    for n in global_node_types:
        for idx,k in enumerate(requests[n]):
            if k[1] > total_offer[n]:
                requests[n][idx][1]=total_offer[n]

    # clean-up requests
    for n in global_node_types:
        requests[n], offers[n] = arb_cleanupRequestsOffers(requests[n], offers[n], n)

    # check offers/requests
    for n in global_node_types:
        if len(pred_values[n]) > 0:
            logger.info(f"predicate values: {n} {pred_values[n]}")
        if len(offers[n]) > 0:
            logger.info(f"offers: {n} {offers[n]}")
        if len(requests[n]) > 0:
            logger.info(f"requests: {n} {requests[n]}")


    logger.info("--- knapsack:")
    # distribution of resources by weights and values
    distribute=dict()
    selected_requests=dict()
    for n in global_node_types:
        distribute[n]=dict()
        selected_requests[n]=list()
    for n in global_node_types:
        # no request or offer for that type of nodes
        if n not in requests.keys() or n not in offers.keys():
            continue
        # compute values and weights
        values = list()
        weights = list()
        all_requests_size = sum([v for name,v in requests[n]])
        for name,req_size in requests[n]:
            if all_requests_size > 0:
               nrr = req_size / all_requests_size * clusters[name]['model']['pw'][0]
            else:
                nrr = 0
            fairshare_exp= - (usage[name][n]['running']/hpc_cap[n])/clusters[name]['model']['share'][n]
            fairshare = 2**fairshare_exp * clusters[name]['model']['pw'][1]
            values.append(int(Parameters.alpha+nrr+fairshare))
            weights.append(req_size)
        # knapsack
        picks, max_val = arb_knapsack_dp(values, weights, len(requests[n]), total_offer[n])
        distribute[n]['picks']=picks
        distribute[n]['profit']=max_val
        for idx in picks:
            selected_requests[n].append(requests[n][idx])
    #print('total_offer',total_offer)
    logger.info(f"distribute: {distribute}")
    logger.info(f"selected_requests: {selected_requests}")
    # create first set of transfer requests
    logger.info("--- transfer requests:")
    #for n in global_node_types:
    #    print("offers ",n, offers[n])
    #    print("selected_requests ",n, selected_requests[n])
    transfer_requests=list()
    for n in global_node_types:
        if n in selected_requests.keys() and n in offers.keys():
           selected_requests[n], offers[n], transfer_requests = arb_create_transfer_requests(selected_requests[n], offers[n], n, transfer_requests, 'knapsack', iteration)
    logger.info(f"knapsack requests: {len(transfer_requests)}")
    for k in transfer_requests:
        logger.info(f"{k['src']} -> {k['dst']} {k['node_type']}:{k['nnodes']}")

    # update transfer requests with a proportional distribution of remaining nodes
    total_load = dict()
    for n in global_node_types:
        total_load[n]=0
        for name in pending_loaded_clusters[n]:
            total_load[n]+=usage[name][n]['pending']
    new_offers=dict()
    remaining_nodes=dict()
    for n in offers.keys():
        new_offers[n] = [ k for k in offers[n] if k[1] > 0 ]
        remaining_nodes[n] = sum([ v for name,v in new_offers[n]])
    new_requests=dict()
    for n in global_node_types:
        new_requests[n]=list()
        for name in pending_loaded_clusters[n]:
            nodes = int(remaining_nodes[n]*usage[name][n]['pending']/total_load[n])
            if nodes > 0:
               new_requests[n].append([name, nodes])
    logger.info(f"remaining_nodes: {remaining_nodes}")

    # check offers/requests
    for n in global_node_types:
        if len(new_offers[n]) > 0:
           logger.info(f" - proportional offers {n} {new_offers[n]}")
        if len(new_requests[n]) > 0:
           logger.info(f" - proportional requests {n} {new_requests[n]}")
    # clean-up requests
    for n in global_node_types:
        new_requests[n],  new_offers[n] = arb_cleanupRequestsOffers(new_requests[n], new_offers[n], n)

    for n in global_node_types:
        if n in new_requests.keys() and n in new_offers.keys():
            new_requests[n], new_offers[n], transfer_requests = arb_create_transfer_requests(new_requests[n], new_offers[n], n, transfer_requests, 'proportional', iteration)
    logger.info(f"proportional requests: {len(transfer_requests)}")
    for k in transfer_requests:
        logger.info(f"{k['src']} -> {k['dst']} {k['node_type']}:{k['nnodes']}")

    #print("--- factorize transfer_requests ---")
    # factorise transfer requests
    #f_transfer_requests = arb_factorize_tranfer_requests(transfer_requests, global_node_types)
    #print("TF factorized:", len(f_transfer_requests))
    #for k in f_transfer_requests:
    #    print(k['src'], k['dst'], k['node_type'], k['nnodes'])
    logger.info(f"-#- resource allocation end {iteration} -#-")
    return transfer_requests
