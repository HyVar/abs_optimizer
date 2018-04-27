pipeline {
  agent any
  options { 
  	buildDiscarder(logRotator(numToKeepStr: '5'))
	disableConcurrentBuilds() 
  }
  stages {
	stage('Test') {
		steps {
			script {
				try {
					// setup worker
					sh 'docker pull jacopomauro/abs_optimizer:latest'
					sh 'docker run -d -p 9001:9001 --name worker_container jacopomauro/abs_optimizer:latest'
			
					// setup controller
					sh 'docker pull jacopomauro/abs_optimizer:main'
					sh 'docker run --net="host" -d --name controller_container jacopomauro/abs_optimizer:main /bin/bash -c "while true; do sleep 60; done"'
			
					// directly run simulation
					sh 'docker exec controller_container python abs_opt.py run --param-file examples/new_years_eve/param_spec.json --abs-file examples/new_years_eve/NewYearsEve.abs --output-log-parser examples/new_years_eve/solution_quality.py --global-simulation-limit 5 --global-timeout 60 --abs-option-l 310'
				}
				finally {
					// cleanup containers ...and try to make sure that both containers are removed in any case
					try {
						sh 'docker stop controller_container'
					}
					finally {
						try {
							sh 'docker rm controller_container'
						}
						finally {
							try {
								sh 'docker stop worker_container'
							}
							finally {
								sh 'docker rm worker_container'
							}
						}
					}
				}
			}
		}
	}
  }
}