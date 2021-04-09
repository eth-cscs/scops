FROM python:3.8-slim-buster
MAINTAINER Maxime Martinasso <maxime.martinasso@cscs.ch>

RUN apt-get update && apt-get -y install --no-install-recommends git wget patch vim bc curl

# set timezone to CET
RUN  ln -sf /usr/share/zoneinfo/CET /etc/localtime

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir /exec
RUN mkdir /data
RUN mkdir /ci_config

WORKDIR /exec

ENTRYPOINT ["./msa.sh"]
