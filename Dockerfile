FROM debian:stable
MAINTAINER Maxime Martinasso <maxime.martinasso@cscs.ch>
ARG SCOPS_USER=scopsuser

ENV SCOPS_USER $SCOPS_USER

# install packages
# Note do not install sudo - sudo does not work within Shifter
RUN apt-get update && apt-get --assume-yes install git wget patch python pkgconf vim bc gtk+2.0 libssl-dev python-pip
#openssh-server

# set timezone to CET
RUN  ln -sf /usr/share/zoneinfo/CET /etc/localtime

# create a user slurm and set mariadb to be user dependent (non-root)
# do not use /home in case it cannot be mounted by the container technology
RUN useradd -ms /bin/bash -d /$SCOPS_USER $SCOPS_USER

# Setup REST Shell
RUN pip install git+https://github.com/treytabner/rest-shell.git && \
    pip install simplejson python-hostlist pandas networkx

USER $SCOPS_USER

# for convenience
RUN mkdir -p /$SCOPS_USER/scops
WORKDIR /$SCOPS_USER/scops
RUN echo "alias vi='vim'" >> /$SCOPS_USER/.bashrc

# Open port for REST Shell
EXPOSE 8080

# invoke shell
CMD ["/bin/bash"]
