import pandas as pd
import time
import datetime
from wlm_executor import wlm_clock, wlm_get_capacity, wlm_get_workload
from ms_utility import timing

def ci_now(location):
    success, cur_clock = wlm_clock(location)
    if not success:
        return -1
    return cur_clock

@timing
def ci_current_load(location, node_types):
    ci_load=dict()
    for n in node_types:
        ci_load[n]=dict()
    ci_load['node_types']=node_types
    ci_load['status']='success'

    success, df_cap = wlm_get_capacity(location)
    if not success:
        return {'status': 'failed'}
    if len(df_cap) == 0:
        for n in node_types:
            ci_load[n]['cap'] = 0
    else:
        df_cap['NODE_TYPE'] = df_cap['AVAIL_FEATURES'].apply(lambda x: x.split(',')[0])
        df_cap['NODE_TYPE_SUM'] = df_cap.groupby('NODE_TYPE')['NODES'].transform('sum')
        df_cap = df_cap[['NODE_TYPE', 'NODE_TYPE_SUM']].drop_duplicates().set_index('NODE_TYPE')
        for n in node_types:
            if n in df_cap.index:
                ci_load[n]['cap'] = df_cap.loc[n, 'NODE_TYPE_SUM']
            else:
                ci_load[n]['cap'] = 0

    success, df = wlm_get_workload(location)
    if not success:
        return {'status': 'failed'}
    if len(df) == 0:
        return ci_load

    success, cur_clock = wlm_clock(location)
    if not success:
        return {'status': 'failed'}

    df['WAIT_TIME'] = cur_clock - df['SUBMIT_TIME'].apply(lambda x: int(time.mktime(datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S").timetuple())))
    wl_node_types = df['FEATURES'].apply(lambda x: x.lower()).unique()
    df_nt=dict()
    for n in wl_node_types:
        df_nt[n]=dict()
        df_nt[n]['PD']=df[(df['FEATURES'] == n) & (df['STATE'] == 'PENDING')]
        df_nt[n]['RN']=df[(df['FEATURES'] == n) & (df['STATE'] == 'RUNNING')]

    for n in wl_node_types:
        ci_load[n]['pending']=df_nt[n]['PD']['NODES'].sum()
        ci_load[n]['running']=df_nt[n]['RN']['NODES'].sum()
        if len(df_nt[n]['PD']) > 0:
            ci_load[n]['max_pending']=df_nt[n]['PD']['NODES'].max()
            ci_load[n]['max_job_wait_time']=df_nt[n]['PD']['WAIT_TIME'].max()
            ci_load[n]['avg_job_wait_time']=int(round(df_nt[n]['PD']['WAIT_TIME'].mean(),0))
        else:
            ci_load[n]['max_pending']=0
            ci_load[n]['max_job_wait_time']=0
            ci_load[n]['avg_job_wait_time']=0
    return ci_load
