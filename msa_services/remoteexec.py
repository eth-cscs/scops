import simplejson
import requests
from logzero import logger
from token_api import secret

def remote_call(location, endpoint, payload=None):
    """ Send HTTP request to API and return output """
    url = f"https://{location}{endpoint}"
    headers = {
       'Content-Type': 'application/json',
       'X-Auth-Token': secret,
    }
    try:
        if payload is None:
            response = requests.post(url, headers=headers, verify=False)
        else:
            response = requests.post(url, data=simplejson.dumps(payload),
                                     headers=headers, verify=False)
    except Exception as err:
        logger.error(f"Error got no valid response, error number: {err}")
        return None

    if response.status_code == 200:
        data = response.json()
        logger.info(f"{data.get('success', '')}")
        return data
    else:
        data = response.json()
        error = data.get('error', "")
        logger.error(f"{response.status_code} - {error}")
        return None

def remote_execute(location, command):
    """ Send HTTP request to API and return output """
    url = f"https://{location}/execute"
    final_command = f"executor \"{command}\""
    payload = {'command': final_command}

    headers = {
       'Content-Type': 'application/json',
       'X-Auth-Token': secret,
    }
    try:
        response = requests.post(url,
                                 data=simplejson.dumps(payload),
                                 headers=headers,
                                 verify=False)
    except Exception as err:
        logger.error(f"Error got no valid response, error number: {err}")
        return None

    if response.status_code == 200:
        data = response.json()
        if data.get('status') != 0:
            status = data.get('status')
            output = data.get('output', '')
            logger.error(f"Error code = {status} : {output}")
            return None
        output = data.get('output', "")
        if isinstance(output, str):
            return output.rstrip()
        else:
            return output
    else:
        logger.error(f"Error to connect to remote interface: status code {response.status_code}")
        return None
