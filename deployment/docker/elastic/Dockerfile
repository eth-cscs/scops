FROM python:3.8-slim-buster
MAINTAINER Maxime Martinasso <maxime.martinasso@cscs.ch>

RUN apt-get update && apt-get -y install --no-install-recommends git wget patch vim bc curl

# set timezone to CET
RUN  ln -sf /usr/share/zoneinfo/CET /etc/localtime

COPY deployment/docker/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD msa_services/elastic_arbiter.py elastic_arbiter.py
ADD msa_services/elastic_ms.py elastic_ms.py
ADD msa_services/elastic_observer.py elastic_observer.py
ADD msa_services/elastic_parameters.py elastic_parameters.py
ADD msa_services/elastic_predicate.py elastic_predicate.py
ADD msa_services/elastic_transfer.py elastic_transfer.py
ADD msa_services/elastic_utility.py elastic_utility.py
ADD msa_services/remoteexec.py remoteexec.py
ADD msa_services/wlm_executor.py wlm_executor.py
ADD msa_services/ms_utility.py ms_utility.py
ADD msa_services/token_api.py token_api.py
ADD msa_services/hwstate_mgr_intf.py hwstate_mgr_intf.py
ADD msa_services/registry_intf.py registry_intf.py

RUN mkdir /data
RUN mkdir /ci_config

ENTRYPOINT ["python3", "./elastic_ms.py"]
