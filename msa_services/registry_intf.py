from remoteexec import remote_call
from logzero import logger

class Registry():

    def __init__(self, location):
        self.location = location

    def register(self, service_type, service_name, service_location):
        endpoint = f"/register/{service_type}/{service_name}/{service_location}"
        data = remote_call(self.location, endpoint)
        return data is not None

    def locate(self, service_name):
        endpoint = f"/locate/{service_name}"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('location')
        return None

    def list(self):
        endpoint = f"/list"
        data = remote_call(self.location, endpoint)
        if data is not None:
            return data.get('services')
        return None
