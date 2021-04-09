import io
import pandas as pd
import re
from hostlist import expand_hostlist, collect_hostlist
from remoteexec import remote_execute
from logzero import logger

def check_command_without_output(command, output):
    if output != "" or output is None:
        logger.error(f"{command} : {output}")
        return False
    return True

def check_command_with_output(command, output):
    if output == "" or output is None:
        logger.error(f"{command} : {output}")
        return False
    return True

def wlm_clock(location):
    command = "ticker -g"
    output = remote_execute(location, command)
    success = check_command_with_output(command, output)
    if success:
        return success, int(output.split(" ")[0])
    return False, -1

def wlm_get_capacity(location):
    command = "sinfo -o '%D|%f' --states=ALLOCATED,IDLE"
    output = remote_execute(location, command)
    success = check_command_with_output(command, output)
    if success:
       df = pd.read_csv(io.StringIO(output), sep='|',error_bad_lines=False)
       return success, df
    return False, None

def wlm_get_workload(location):
    command = "squeue --states=pd,r -o '%V|%D|%f|%T' -S V"
    output = remote_execute(location, command)
    success = check_command_with_output(command, output)
    if success:
       df = pd.read_csv(io.StringIO(output), sep='|',error_bad_lines=False)
       return success, df
    return False, None

def wlm_set_nodes_state(location, nodelist, state):
    command = f"scontrol update NodeName={nodelist} state={state} Reason='scops elasticity'"
    output = remote_execute(location, command)
    return check_command_without_output(command, output)

def wlm_submit_reservation_jobs(location, task_id, nnodes, node_type):
    job_size=20
    job_name=f"scops-{task_id}"
    command = f"relocate {node_type} {nnodes} {job_name} {job_size}"
    output = remote_execute(location, command)
    return check_command_with_output(command, output)

def wlm_cancel_reservation_jobs(location, task_id):
    command = f"scancel --name scops-{task_id}"
    output = remote_execute(location, command)
    return check_command_without_output(command, output)

def wlm_get_nodes_in_reservation(location, task_id, task_node_type):
    command = f"rsvnodelist scops-{task_id}"
    output = remote_execute(location, command)
    success = check_command_with_output(command, output)
    if success:
        if output.startswith('No nodelist') or output.startswith('No reservation'):
            return success, "", 0
        splitted_output = re.split('\n',output)
        resources=list()
        for t in splitted_output:
            node_type, nodelist = t.split(' ')
            if task_node_type in node_type.split(','): # should always be true
                resources+=expand_hostlist(nodelist)
        return success, collect_hostlist(resources), len(resources)
    return False, None, 0

def wlm_cleanup_reservation(location, task_id):
    command = f"cleanup scops-{task_id}"
    output = remote_execute(location, command)
    return output

def wlm_extract_nodes_from_reservation(location, task_id, nodelist):
    success = wlm_set_nodes_state(location, nodelist, "DOWN")
    if not success:
        return False
    command = f"rsvmgt scops-{task_id} - {nodelist}"
    output = remote_execute(location, command)
    if (output != "" and output != "Reservation updated.") or output is None:
        logger.error(f"{command} : {output}")
        return False
    return True
