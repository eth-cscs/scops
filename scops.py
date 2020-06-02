import os
import pandas as pd
import numpy as np
from datetime import datetime
import time
import urllib3
from parameters import Parameters
from arbiter import ScopsArbiter
from dispatcher import ScopsDispatcher
from cluster import Cluster
from observer import SlurmResourceObserver
from broker import SlurmResourceBroker
from predicate import MaxJobWaitTimeDayNight, AvgJobWaitTime, ConstValue, QuotaAvailableAllowBigJob, ConstValueIfPending
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
pd.set_option('display.max_columns', None)

def appendFromUsage(df, div_now, iteration, usage):
    new_df = df
    usage_df_dict=dict()
    for name in usage.keys():
        usage_df_dict['cluster']=name
        usage_df_dict['now']=div_now[name]
        usage_df_dict['iteration']=iteration
        usage_df_dict['status']=usage[name]['status']
        if 'node_types' in usage[name]:
            for n in usage[name]['node_types']:
                usage_df_dict['node_type']=n
                list_key=['cap', 'max_pending', 'pending', 'running', 'max_job_wait_time', 'avg_job_wait_time']
                for h in list_key:
                    if h in usage[name][n]:
                        usage_df_dict[h]=usage[name][n][h]
                    else:
                        usage_df_dict[h]=np.nan
                new_df = new_df.append(usage_df_dict, ignore_index=True)
        else:
            new_df = new_df.append(usage_df_dict, ignore_index=True)
    if len(usage_df_dict) > 0:
        return new_df
    else:
        return df

def appendFromRequest(df, div_now, requests):
    if len(requests) == 0:
        return df
    for r in requests:
        r['now']=div_now[r['src']]
    new_df = df.append(requests, ignore_index=True)
    return new_df

def printusage(usage, indent=1):
    for name in usage:
        print(name+"-"+usage[name]['status'])
        if usage[name]['status'] == 'success':
            for n in usage[name]['node_types']:
                 str_us=' '*indent+n
                 order=['cap', 'running', 'pending', 'max_pending', 'max_job_wait_time', 'avg_job_wait_time' ]
                 for k in order:
                    if k in usage[name][n]:
                       str_us+=' %s=%d' % (k, usage[name][n][k])
                 print(str_us)


os.environ["TOKEN"] = "anyword"
hosts=dict()
hosts['ault01']="111.111.111.72"
hosts['ault02']="111.111.111.73"
hosts['ault03']="111.111.111.74"
hosts['ault04']="111.111.111.75"
hosts['ault16']="111.111.111.87"
hosts['ault17']="111.111.111.88"
hosts['ault18']="111.111.111.89"
hosts['ault19']="111.111.111.90"
port=44501
global_node_types=['gpu', 'mc']
hpc_cap={'gpu': 5688, 'mc': 1630}
weight_mult=Parameters.weight_mult
group_accounts=dict()
                       # 1 cabinet (192 nodes)
group_accounts['CE']={ 'acc': ['CE_ich', 'CE_uzh'],\
                       'pw': [10*weight_mult,10*weight_mult],\
                       'share': {'mc': 0.11, 'gpu': 0},\
                       'pred': QuotaAvailableAllowBigJob, \
                       'pred_value': [ 192 ]
                       }
                       # about 5 nodes
group_accounts['CI']={ 'acc': ['CI'],\
                       'pw': [5*weight_mult,5*weight_mult],\
                       'share': { 'mc': 0.003, 'gpu': 0.0009},\
                       'pred': MaxJobWaitTimeDayNight,\
                       'pred_value': [3600, 4*3600] \
                       }
                       # what's left
group_accounts['PA']={ 'acc': ['PA_pr', 'PA_ul', 'PA_rest'],\
                       'pw': [5*weight_mult,5*weight_mult],\
                       'share': {'mc': 0.19, 'gpu': 0.25},\
                       'pred': ConstValue,\
                       'pred_value': [ True ]
                       }
                       # about 80 nodes
group_accounts['PT']={ 'acc': ['PT_em', 'PT_eth', 'PT_mr', 'PT_u'],\
                       'pw': [10*weight_mult,10*weight_mult],\
                       'share': { 'mc': 0.05, 'gpu': 0.24},\
                       'pred': AvgJobWaitTime,\
                       'pred_value': [ 4*3600 ]
                       }
group_accounts['UC']={ 'acc': ['IC_urg'],\
                       'pw': [100*weight_mult,100*weight_mult],\
                       'share': { 'mc': 0.0, 'gpu': 1.0},\
                       'pred': ConstValueIfPending,\
                       'pred_value': [ False ]
                       }
acct_resource=dict()
acct_resource['CE_ich']=['mc']
acct_resource['CE_uzh']=['mc']
acct_resource['CI']=['mc', 'gpu']
acct_resource['PA_pr']=['gpu']
acct_resource['PA_rest']=['mc', 'gpu']
acct_resource['PA_ul']=['mc', 'gpu']
acct_resource['PT_em']=['mc']
acct_resource['PT_eth']=['mc', 'gpu']
acct_resource['PT_mr']=['mc']
acct_resource['PT_u']=['mc']
acct_resource['IC_urg']=['gpu']

location_host=dict()
location_host['CE_ich'] = hosts['ault16']+':44501'
location_host['CE_uzh'] = hosts['ault16']+':44511'
location_host['CI']     = hosts['ault16']+':44521'
location_host['IC_urg'] = hosts['ault16']+':44531'
location_host['PA_pr']  = hosts['ault17']+':44541'
location_host['PA_rest']= hosts['ault17']+':44551'
location_host['PA_ul']  = hosts['ault18']+':44561'
location_host['PT_em']  = hosts['ault19']+':44571'
location_host['PT_eth'] = hosts['ault19']+':44581'
location_host['PT_mr']  = hosts['ault19']+':44591'
location_host['PT_u']   = hosts['ault19']+':44601'
clusters= dict()
for g in group_accounts:
    ga = group_accounts[g]
    for a in ga['acc']:
        print(a, location_host[a])
        clusters[a] = Cluster(location=location_host[a], \
                              priority_w=ga['pw'], \
                              share=ga['share'], \
                              predicate=ga['pred'], \
                              predicate_values=ga['pred_value'], \
                              node_types=acct_resource[a], \
                              observer=SlurmResourceObserver(), \
                              broker=SlurmResourceBroker())
        port+=10

clock_rate=Parameters.clock_rate
iteration_elaspedTime=int(Parameters.iteration_elaspedTime*clock_rate)

SA = ScopsArbiter(total_resource=hpc_cap)
DI = ScopsDispatcher(clock_rate)

iteration=0
df_out_divclock = pd.DataFrame(columns=['iteration', 'min', 'max']+clusters.keys())
df_out_usage = pd.DataFrame(columns=['iteration', 'now', 'node_type', 'cluster', 'max_pending', 'pending', 'running', 'cap', 'max_job_wait_time', 'avg_job_wait_time', 'status'])
df_out_request = pd.DataFrame(columns=['iteration', 'now', 'node_type', 'src', 'dst', 'nnodes', 'init_nnodes', 'nodelist', 'id', 'ts_request', 'ts_addnodes', 'ts_removenodes', 'ts_cancel', 'ts_check', 'ts_transfer', 'ts_terminate', 'terminated', 'algo', 'status', 'reason'])
while True:
    print("[SC%d] scop iteration=%d" % (iteration, iteration))
    ts = time.time()
    ts_all = time.time()

    # cluster instance time divergence
    div_now=dict()
    for k in clusters:
        div_now[k]=clusters[k].now()
    if len([x for x in div_now.values() if x > 0]) > 0:
       min_c = min([x for x in div_now.values() if x > 0])
       max_c = max([x for x in div_now.values()])
       div_now['iteration']=iteration
       div_now['min']=min_c
       div_now['max']=max_c
       df_out_divclock = df_out_divclock.append(div_now, ignore_index=True)
       print("[SC%d] - [%s] Clock div: %d" % ( iteration, datetime.fromtimestamp(min_c), max_c-min_c))
    else:
        if iteration == 0:
           continue
    df_out_divclock.to_pickle('scops_df_out_divclock.pickle')

    # identify clusters' usage
    observer_usage = DI.getClustersUsage(clusters)
    printusage(observer_usage)
    df_out_usage = appendFromUsage(df_out_usage, div_now, iteration, observer_usage)
    df_out_usage.to_pickle('scops_df_out_usage.pickle')

    # check if capacity is correct?
    # false positive if observer cannot get data
    # false positive if drain nodes are set
    check_cap={ 'gpu': 0, 'mc': 0}
    for name in observer_usage.keys():
        if 'node_types' in observer_usage[name]:
            for n in observer_usage[name]['node_types']:
                check_cap[n]+=observer_usage[name][n]['cap']
    for n in global_node_types:
        if check_cap[n] != hpc_cap[n]:
            print("[SC%d] [warning] %s capacity different %d != %d" % (iteration, n, check_cap[n], hpc_cap[n]))


    # resource distribution
    transfer_requests = SA.distributeResources(observer_usage, clusters, global_node_types, iteration)
    total_requested_nodes={'gpu': 0, 'mc': 0}
    print("[SC%d] Transfer requests" % (iteration))
    for k in transfer_requests:
        print("[SC"+str(iteration)+"] [TR] "+k['src']+'->'+k['dst']+' '+str(k['nnodes'])+k['node_type']+' '+k['algo']+' '+k['id'])
        total_requested_nodes[k['node_type']]+=k['nnodes']

    # execute resource transfer
    executed_requests = DI.executeTransfers(transfer_requests, clusters, iteration)
    df_out_request = appendFromRequest(df_out_request, div_now, executed_requests)
    df_out_request.to_pickle('scops_df_out_request.pickle')
    print("[SC%d] Executed requests" % (iteration))
    total_remaining_nodes={'gpu': 0, 'mc': 0}
    for k in executed_requests:
        print("[SC"+str(iteration)+"] [ER] "+k['src']+'->'+k['dst']+' '+str(k['nnodes'])+k['node_type']+' '+k['status']+' '+k['id'])
        total_remaining_nodes[k['node_type']]+=k['nnodes']
    print("[SC%d] total_requested_nodes=%s, total_remaining_nodes=%s" % (iteration, total_requested_nodes, total_remaining_nodes))

    # wait next iteration
    te = time.time()
    wait_nextIteration = iteration_elaspedTime - (te - ts)
    if wait_nextIteration > 0:
       print("[SC%d] Wait next iteration %d real seconds" % (iteration, wait_nextIteration))
       for k in range(0,Parameters.n_pokes):
           ts = time.time()
           for k in clusters:
               div_now[k]=clusters[k].now()
           observer_usage = DI.getClustersUsage(clusters)
           df_out_usage = appendFromUsage(df_out_usage, div_now, iteration, observer_usage)
           df_out_usage.to_pickle('scops_df_out_usage.pickle')
           te = time.time()
           poke_wait = int(wait_nextIteration/Parameters.n_pokes) - (te - ts)
           if poke_wait > 0:
              print("[SC%d]     next poke in %d real seconds" % (iteration, poke_wait))
              time.sleep(poke_wait)
    DI.cleanupIteration(clusters, executed_requests)
    iteration+=1
    te_all = time.time()
    print("[SC%d] Iteration lasted %d real seconds" % (iteration, te_all - ts_all))


