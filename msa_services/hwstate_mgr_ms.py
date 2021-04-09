import argparse
import uuid
from flask import Flask, jsonify, request
from logzero import logger, logfile
from ms_utility import check_apikey
from registry_intf import Registry
from wlm_executor import wlm_cleanup_reservation, wlm_extract_nodes_from_reservation, wlm_cancel_reservation_jobs, wlm_get_nodes_in_reservation, wlm_set_nodes_state, wlm_submit_reservation_jobs
import pandas as pd
import signal
import pickle
import os

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask("HW State Manager")

registry = None
ci_cached = dict()
tasks = dict()

def trap(signum, frame):
    filename = "hwstate_mgr_tasks.pickle"
    if os.path.isdir('/data'):
        filename=f"/data/{filename}"
    with open(filename,"wb") as f:
        pickle.dump(tasks, f)
    logger.info(f"Signal: {signum}, exiting.")
    exit(0)

def getci_location(ci_name):
    global ci_cached
    global registry
    if ci_name not in ci_cached:
        ci_location = registry.locate(ci_name)
        ci_cached[ci_name] = ci_location
    return ci_cached[ci_name]

def task_get_location(task_id):
    global tasks
    if task_id not in tasks.keys():
        return None, jsonify(error="Task id not found")
    task = tasks[task_id]
    ci_name = task['target']
    ci_location = getci_location(ci_name)
    if ci_location is None:
        tasks[task_id]['status'] = 'error'
        return None, jsonify(error=f"Cannot find target {ci_name}.")
    return task, ci_location

def create_task(task_type, task_target, task_param):
    global tasks
    task_id = str(uuid.uuid4().hex)
    status = 'queued'
    tasks[task_id] = {'status': status, 'param': task_param,
                      'type': task_type, 'target': task_target}
    return task_id

def set_status(task_id, status):
    global tasks
    tasks[task_id]['status'] = status

def set_param(task_id, nodelist, nnodes):
    global tasks
    tasks[task_id]['param']['nodelist'] = nodelist
    tasks[task_id]['param']['nnodes'] = nnodes

@app.route('/tasklist', methods=['POST'])
@check_apikey
def tasklist():
    global tasks
    return jsonify(success="List of tasks.", tasks=tasks), 200

@app.route('/task/<string:task_id>', methods=['POST'])
@check_apikey
def task(task_id):
    task, ci_location = task_get_location(task_id)
    if task is None:
        return ci_location, 400
    if task['status'] in ['completed', 'canceled']:
        msg = f"Task {task_id} is {task['status']}"
        if 'nodelist' in task['param']:
            nodelist = task['param']['nodelist']
        else:
            nodelist = ''
        if 'nnodes' in task['param']:
            nnodes = task['param']['nnodes']
        else:
            nnodes = 0
        return jsonify(success=msg, status=task['status'], nodelist=nodelist, nnodes=nnodes), 200
    if task['status'] == 'error':
        msg = f"Task {task_id} terminated with an error"
        nodelist = ""
        nnodes = -1
        return jsonify(success=msg, status='error', nodelist=nodelist, nnodes=nnodes), 200
    success, nodelist, nnodes = wlm_get_nodes_in_reservation(ci_location, task_id, task['param']['node_type'])
    if success:
        if nnodes < task['param']['nnodes']:
            status = 'in progress'
        else:
            status = 'completed'
        msg = f"Task {task_id} is {status}, {nnodes} over {task['param']['nnodes']}"
        set_status(task_id, status)
        return jsonify(success=msg, status=status, nodelist=nodelist, nnodes=nnodes), 200
    set_status(task_id, 'error')
    return jsonify(error=f"Error for task {task_id}"), 400

@app.route('/reservenodes/<string:ci_name>/<int:nnodes>/<string:node_type>', methods=['POST'])
@check_apikey
def reservenodes(ci_name, nnodes, node_type):
    task_id = create_task('get', ci_name, {'nnodes': nnodes, 'node_type': node_type})
    task, ci_location = task_get_location(task_id)
    if task is None:
        return ci_location, 400
    success = wlm_submit_reservation_jobs(ci_location, task_id, nnodes, node_type)
    if success:
        return jsonify(success=f"Task {task_id}: started", task_id=task_id), 200
    set_status(task_id, 'error')
    return jsonify(error=f"Task {task_id}: failed"), 400

@app.route('/extractnodes/<string:task_id>', methods=['POST'])
@check_apikey
def extractnodes(task_id):
    task, ci_location = task_get_location(task_id)
    if task is None:
        return ci_location, 400
    success, nodelist, nnodes = wlm_get_nodes_in_reservation(ci_location, task_id, task['param']['node_type'])
    if success:
        success = wlm_extract_nodes_from_reservation(ci_location, task_id, nodelist)
        if success:
            return jsonify(success=f"Task {task_id}: {nodelist} extracted", nodelist=nodelist), 200
    set_status(task_id, 'error')
    return jsonify(error=f"Task {task_id}: cannot extract nodes", task_id=task_id), 400

@app.route('/cancel/<string:task_id>', methods=['POST'])
@check_apikey
def cancel(task_id):
    task, ci_location = task_get_location(task_id)
    if task is None:
        return ci_location, 400
    success, nodelist, nnodes = wlm_get_nodes_in_reservation(ci_location, task_id, task['param']['node_type'])
    if success:
        set_param(task_id, nodelist, nnodes)
    success = wlm_cancel_reservation_jobs(ci_location, task_id)
    if success:
        set_status(task_id, 'canceled')
        return jsonify(success=f"Task {task_id}: canceled."), 200
    set_status(task_id, 'error')
    return jsonify(error=f"Task {task_id}: failed to cancel"), 400

@app.route('/terminate/<string:task_id>', methods=['POST'])
@check_apikey
def terminate(task_id):
    task, ci_location = task_get_location(task_id)
    if task is None:
        return ci_location, 400
    output = wlm_cleanup_reservation(ci_location, task_id)
    set_status(task_id, 'terminated')
    return jsonify(success=f"Task id {task_id} terminate.", output=output), 200

@app.route('/setnodes/<string:ci_name>', methods=['POST'])
@check_apikey
def setnodes(ci_name):
    nodelist = request.data.decode("utf-8")
    ci_location = getci_location(ci_name)
    if ci_location is not None:
        success = wlm_set_nodes_state(ci_location, nodelist, "RESUME")
        if success:
            return jsonify(success=f"nodes {nodelist} sets to RESUME on {ci_name}"), 200
    return jsonify(error=f"Unable to change state to RESUME for {nodelist} on {ci_name}"), 401

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", action="store", default="12010")
    parser.add_argument("-r", "--registry", action="store", default="register:12000")

    signal.signal(signal.SIGINT, trap)
    signal.signal(signal.SIGABRT, trap)
    signal.signal(signal.SIGTERM, trap)

    args = parser.parse_args()
    port = int(args.port)
    registry = Registry(args.registry)
    logfile("/data/hwstate_mgr_ms.log")

    app.run(host="0.0.0.0", port=port, ssl_context='adhoc', use_reloader=False)
