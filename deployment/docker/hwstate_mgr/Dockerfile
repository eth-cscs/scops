FROM python:3.8-slim-buster
MAINTAINER Maxime Martinasso <maxime.martinasso@cscs.ch>

RUN apt-get update && apt-get -y install --no-install-recommends git wget patch vim bc curl

# set timezone to CET
RUN  ln -sf /usr/share/zoneinfo/CET /etc/localtime

COPY deployment/docker/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD msa_services/hwstate_mgr_ms.py hwstate_mgr_ms.py
ADD msa_services/registry_intf.py registry_intf.py
ADD msa_services/remoteexec.py remoteexec.py
ADD msa_services/wlm_executor.py wlm_executor.py
ADD msa_services/ms_utility.py ms_utility.py
ADD msa_services/token_api.py token_api.py

RUN mkdir /data

ENTRYPOINT ["python3", "hwstate_mgr_ms.py"]
