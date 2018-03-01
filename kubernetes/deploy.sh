
# create namespace myapp-namespace and rbac rules
kubectl apply -f rbac_rules_namespace.yml

# create default ingress returning 404
kubectl apply -f ingress_default_backend.yaml

# create the services (replication number to be configured. Default is 1)
# to scale run the command "kubectl scale deployment http-myapp --replicas=<NUM>"
kubectl apply -f http_myapp.yaml

# deploy haproxy-controller
kubectl apply -f haproxy_ingress.yaml

# the haproxy is esposed as a NodePort
# to retreive the port number to reach it run the following command
kubectl --namespace=myapp-namespace get services | grep haproxy-ingress

#to test
# curl -H 'Host: myapp' http://IP:PORT/OPERATION
# the ip is one of the IPs of the nodes of the cluster
# the port is the NodePort used to redirect port 80
# the OPERATION is the operation name to be invoked
