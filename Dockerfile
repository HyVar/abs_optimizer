FROM ubuntu
MAINTAINER Jacopo Mauro

COPY ./ /abs_code

RUN apt-get update && apt-get install -y \
		wget && \
		wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb && \
		dpkg -i erlang-solutions_1.0_all.deb && \
		apt-get update && apt-get install -y \
		make \
		git \
		default-jdk \
		python-dev \
		erlang-base \
		ant \
		screen \
		nano && \
	cd / && \
	git clone --depth=1 https://github.com/abstools/abstools.git && \
	cd abstools && \
	make 

ENV PATH /abstools/frontend/bin/bash:$PATH
WORKDIR /abs_code
