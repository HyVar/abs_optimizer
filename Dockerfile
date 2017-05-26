FROM ubuntu
MAINTAINER Jacopo Mauro

COPY ./ /abs_code

RUN apt-get update && apt-get install -y \
		make \
		git \
		default-jdk \
		python-dev \
		erlang \
		ant \
		screen \
		nano && \
	cd / && \
	git clone --depth=1 https://github.com/abstools/abstools.git && \
	cd abstools && \
	make 

ENV PATH /abstools/frontend/bin/bash:$PATH
WORKDIR /abs_code
