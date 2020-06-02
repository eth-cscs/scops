import time
import datetime
import io
import pandas as pd
from remoteexec import remote_execute


def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print("%s function took %0.3f ms" % (f.func_name, (time2-time1)*1000.0))
        return ret
    return wrap

class SlurmResourceObserver:

    def __init__(self):
       pass

    def getSystemClock(self, location):
        command = "ticker -g"
        output = remote_execute(location, command)
        if output == "" or output is None:
            print("Can get cluster clock.")
            return -1
        return int(output.split(" ")[0])

    def getJobsUsage(self, location, cluster_node_types):
        cur_clock = self.getSystemClock(location)
        if cur_clock < 0:
            print("No usable cluster clock.")
            return {'status': 'failed'}
        usage=dict()
        for n in cluster_node_types:
            usage[n]=dict()
        usage['node_types']=cluster_node_types
        usage['status']='success'

        # get capacity
        command = "sinfo -o '%D|%f' --states=ALLOCATED,IDLE"
        output = remote_execute(location, command)
        if output == "" or output is None:
            print("Command failed: %s" % command)
            return {'status': 'failed'}
        df_nodes = pd.read_csv(io.StringIO(output), sep='|',error_bad_lines=False)
        df_nodes['NODE_TYPE']=df_nodes['AVAIL_FEATURES'].apply(lambda x: x.split(',')[0])
        nodes_sum = df_nodes.groupby('NODE_TYPE')['NODES'].sum()
        # no capacity can be found, no nodes (all down or reserved) while jobs pending
        capacity_node_types=list(df_nodes['NODE_TYPE'].unique())
        for n in cluster_node_types:
            if n in capacity_node_types:
                usage[n]['cap']=nodes_sum.loc[n]
            else:
                usage[n]['cap']=0

        # get workoad
        command = "squeue --states=pd,r -o '%V|%D|%f|%T' -S V"
        output = remote_execute(location, command)
        if output == "" or output is None:
            print("No usable output for command: %s" % command)
            return {'status': 'failed'}
        df = pd.read_csv(io.StringIO(output), sep='|',error_bad_lines=False)

        # no workload
        if len(df) == 0:
            return usage

        # identify workload
        df['WAIT_TIME']=cur_clock-df['SUBMIT_TIME'].apply(lambda x: int(time.mktime(datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S").timetuple())))
        wl_node_types=df['FEATURES'].apply(lambda x: x.lower()).unique()
        df_nt=dict()
        for n in wl_node_types:
            df_nt[n]=dict()
            df_nt[n]['PD']=df[(df['FEATURES'] == n) & (df['STATE'] == 'PENDING')]
            df_nt[n]['RN']=df[(df['FEATURES'] == n) & (df['STATE'] == 'RUNNING')]

        for n in wl_node_types:
            usage[n]['pending']=df_nt[n]['PD']['NODES'].sum()
            usage[n]['running']=df_nt[n]['RN']['NODES'].sum()
            if len(df_nt[n]['PD']) > 0:
                usage[n]['max_pending']=df_nt[n]['PD']['NODES'].max()
                usage[n]['max_job_wait_time']=df_nt[n]['PD']['WAIT_TIME'].max()
                usage[n]['avg_job_wait_time']=int(round(df_nt[n]['PD']['WAIT_TIME'].mean(),0))
            else:
                usage[n]['max_pending']=0
                usage[n]['max_job_wait_time']=0
                usage[n]['avg_job_wait_time']=0
        return usage

