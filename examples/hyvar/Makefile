
all: run			## Generate data and start model (default)

Settings.abs: generate_settings.py # generate the data file
	python generate_settings.py > Settings.abs

compile: Settings.abs	HyVarSym.abs	## Compile the model
	absc -erlang HyVarSym.abs Settings.abs

run: compile
	-rm gen/erl/absmodel/priv/index.html
	ln -s `pwd`/index.html gen/erl/absmodel/priv/index.html
	#cp index.html gen/erl/absmodel/priv/index.html
	cp -r static/* gen/erl/absmodel/priv/static
	gen/erl/run -p 8080

help:				## Display this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
