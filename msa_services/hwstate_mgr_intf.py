from remoteexec import remote_call

class HWState_mgr():

    def __init__(self, location):
        self.location = location

    def task(self, task_id):
        endpoint = f"/task/{task_id}"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('status'), data.get('nodelist'), data.get('nnodes')
        return 'error', None, None

    def tasklist(self):
        endpoint = f"/tasklist"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('tasks')
        return None

    def reservenodes(self, ci_name, nnodes, node_type):
        endpoint = f"/reservenodes/{ci_name}/{nnodes}/{node_type}"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('task_id')
        return None

    def extractnodes(self, task_id):
        endpoint = f"/extractnodes/{task_id}"
        data = remote_call(self.location, endpoint)
        if data is not None:
           return data.get('nodelist')
        return None

    def cancel(self, task_id):
        endpoint = f"/cancel/{task_id}"
        data = remote_call(self.location, endpoint)
        return data is not None

    def terminate(self, task_id):
        endpoint = f"/terminate/{task_id}"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('output')
        return None

    def setnodes(self, ci_name, nodelist):
        endpoint = f"/setnodes/{ci_name}"
        data = remote_call(self.location, endpoint, payload=nodelist)
        return data is not None
