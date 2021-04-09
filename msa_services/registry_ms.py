import argparse
from flask import Flask, jsonify
from logzero import logger, logfile
from ms_utility import check_apikey

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask("Registry")
service_types = [ 'ci', 'msa' ]
registry = dict()
for t in service_types:
      registry[t] = dict()

@app.route('/register/<string:service_type>/<string:service_name>/<string:location>', methods=['POST'])
@check_apikey
def register(service_type, service_name, location):
    global registry
    if service_type in service_types:
       registry[service_type][service_name] = location
       return jsonify(success=f"service {service_name} registered at {location}"), 200
    return jsonify(error=f"Service type {service_type} unknown"), 503

@app.route('/locate/<string:service_name>', methods=['POST'])
@check_apikey
def locate(service_name):
    global registry
    for k in service_types:
        if service_name in registry[k]:
            return jsonify(success=f"Service {service_name} located.", location=registry[k][service_name]), 200
    return jsonify(error=f"service {service_name} not found in registry"), 404

@app.route('/list', methods=['POST'])
@check_apikey
def list():
    global registry
    return jsonify(success="List of services.", services=registry), 200

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", action="store", default="12000")

    args = parser.parse_args()
    port = int(args.port)

    logfile("/data/register_ms.log")

    app.run(host="0.0.0.0", port=port, use_reloader=False, ssl_context='adhoc')

