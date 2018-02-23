FROM python:3-stretch
MAINTAINER Jacopo Mauro

# docker image that allows to run the abs optimizer with SMAC3 exploiting 
# external images able to run the simulation


# install dependencies and useful commands
RUN \
	# install packages 
	apt-get update && \
  apt-get install -y \
			screen \
			swig \
			nano && \
  rm -rf /var/lib/apt/lists/* && \
	pip install Cython \
		numpy && \
	# pip has some dependencies problems in doing everything in one step
  # that is why we do it in multiple steps
	pip install \
			click \
			requests \
			smac

# clone abs_optimizer
RUN git clone --depth=1 -b demonstrator2 https://github.com/HyVar/abs_optimizer.git

WORKDIR /abs_optimizer


