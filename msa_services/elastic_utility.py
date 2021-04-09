import pandas as pd
import numpy as np
from logzero import logger

pd.set_option('display.max_columns', None)

df_out_divclock = pd.DataFrame(columns=['iteration', 'min_c', 'min_v', 'max_c', 'max_v'])

df_out_usage = pd.DataFrame(columns=['iteration', 'now', 'node_type', 'cluster', 'max_pending', 'pending', 'running', 'cap', 'max_job_wait_time', 'avg_job_wait_time', 'status'])

df_out_request = pd.DataFrame(columns=['iteration', 'now', 'node_type', 'src', 'dst', 'nnodes', 'nnodes_transferred', 'nodelist', 'id', 'terminated', 'algo', 'status'])

def append_usage(div_now, iteration, usage):
    global df_out_usage
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
                df_out_usage = df_out_usage.append(usage_df_dict, ignore_index=True)
        else:
            df_out_usage = df_out_usage.append(usage_df_dict, ignore_index=True)
    df_out_usage.to_pickle('/data/scops_df_out_usage.pickle')

def append_request(div_now, requests):
    global df_out_request
    if len(requests) > 0:
        for r in requests:
            r['now']=div_now[r['src']]
        df_out_request = df_out_request.append(requests, ignore_index=True)
        df_out_request.to_pickle('/data/scops_df_out_request.pickle')

def append_divclock(div_now):
    global df_out_divclock
    if len(div_now) > 0:
        df_out_divclock = df_out_divclock.append(div_now, ignore_index=True)
        df_out_divclock.to_pickle('/data/scops_df_out_divclock.pickle')

def print_usage(usage, iteration, indent=1):
    logger.info(f"[IT{iteration}] workload:")
    for name in usage:
        logger.info(f"{name}-{usage[name]['status']}")
        if usage[name]['status'] == 'success':
            for n in usage[name]['node_types']:
                 str_us=' '*indent+n
                 order=['cap', 'running', 'pending', 'max_pending', 'max_job_wait_time', 'avg_job_wait_time' ]
                 for k in order:
                    if k in usage[name][n]:
                       str_us+=f" {k}={usage[name][n][k]}"
                 logger.info(str_us)

