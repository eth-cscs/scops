import simplejson
import os
import requests

def remote_execute(location, command):
        """ Send HTTP request to API and return output """
        endpoint = "https://%s/execute" % location
        final_command = "executor \"%s\"" % command
        payload = {'command': final_command}
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': os.environ.get('TOKEN'),
        }
        #print("Execute: %s" % final_command)

        try:
            response = requests.post(endpoint,
                                     data=simplejson.dumps(payload),
                                     headers=headers,
                                     verify=False)
        except Exception as err:
            print("Error got no valid response, error number: %s" % str(err))
            return None

        if response.status_code == 200:
            data = response.json()
            if data.get('status') != 0:
                print("Error code = %d : %s" % (data.get('status'), data.get('output', "")))
                return None
            output = data.get('output', "")
            return output.rstrip()
        else:
            print("Error to connect to remote interface: status code %d" % response.status_code)
            return None
