import argparse
from registry_intf import Registry
from remoteexec import remote_execute

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-ci", "--ci", action="store")
    parser.add_argument("-cmd", "--command", action="store")
    parser.add_argument("-r", "--registry", action="store", default="0.0.0.0:12000")

    args = parser.parse_args()
    ci_name = args.ci
    command = args.command
    #reg = Registry(args.registry)
    #ci_location = reg.locate(ci_name)
    ci_location = "0.0.0.0:17101"

    if ci_location:
        output = remote_execute(ci_location, command)
        print(f"{ci_name}: {command}")
        print(output)
