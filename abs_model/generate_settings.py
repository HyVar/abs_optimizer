import math

# the instance speed in ms
instance_base_speed = 1000

# average times in ms
avg_times = [30,1500,30,70 + 500 + 255,33500]

# init time for instances in ms
instance_init_times = [0, (33 + 420)*1000,0,0,(32 + 349)*1000]

# scaling of average running times (x ms is equal to 1 time slot)
time_scaling_factor = 1000.0

# every time windows is equivalent to x milliseconds
# check also the average_times variable
time_window = 15 * 60 * 1000 / time_scaling_factor

# number of jobs submitted every time window
# note thet here we assume a mapping 1s <-> 15s of real time
jobs_per_time_window =  [19,19,16,13,12,11,10,10,10,9,11,10,19,16,18,15,15,20,38,36,
    46,73,103,95,107,139,198,221,265,270,287,326,334,326,304,259,
    251,231,221,191,172,174,171,161,163,162,169,158,156,173,
    169,166,167,174,170,165,167,163,180,179,186,177,203,193,
    234,246,251,235,262,280,276,267,253,220,201,166,151,137,
    126,105,90,93,76,67,74,75,68,64,71,65,50,42,40,31,28,27,]
jobs_per_time_window = [3*x for x in jobs_per_time_window]

# if components are more powerful specify them here
instance_speed = [1000,1000,1000,3000,1000]

# speed consumption after which instances may switch jobs
switch_time_slot = 500

# checking_avg_time_interval (in time slots)
checking_avg_time_interval = 60

# cooling off in time slots (multiple of checking_avg_time_interval)
cooling_off_time = [300,360,300,300,480]

# initial instances per component
initial_instances = [1] * len(avg_times)
#initial_instances = [1,2,1,1,13]

# x scale in factor in ms
scaling_in = [ 1000* x for x in [1000,219,1000,1000,192]]
scaling_in = [max(x,1000.0) for x in scaling_in]

# x scale out factor in ms
scaling_out = [ 1000* x for x in [999,111,999,999,106]]
scaling_out = [max(0,x) for x in scaling_out]

# amount of instance to increase every scale in
scale_in_amount_list = [0,1,0,0,1]
#scale_in_amount_list = [0]*5
# amount of instance to decrease every scale out
scale_out_amount_list = [0,2,0,0,2]
#scale_out_amount_list = [0]*5
# drop requests x-> discard x and keep the x + 1
drop_requests = [0,0,3,0,0]


#scaling_down_ratio (RAT)
# pending_jobs <  size(keys(instances)) * scaling_down_ratio
# allows the scalind down
scaling_down_ratio = ["0","25","0","0","20/20"]

#max_conn (0 means infinite) 
max_conn = [0,30,0,0,2]

# parallel_part
parallel_cost = [0,0,0,0,0]

print "module Settings;"
print "export *;\n" 

# note thet here we assume a mapping 1s <-> 1s of real time
average_times = [ int(math.ceil(x * instance_base_speed / time_scaling_factor)) for x in avg_times]
instance_init_time_slots = [ int(math.ceil(x / instance_base_speed)) for x in instance_init_times]

# switch_time_slot
print "def Int switch_time_slot() = ",
print switch_time_slot,
print ";\n"

# checking_avg_time_interval (in time slots)
print "def Int checking_avg_time_interval() = ",
print checking_avg_time_interval,
print ";\n"

# cooling_off_time
for i in range(len(cooling_off_time)):
    print "def Int cooling_off_time_" + unicode(i) + "() = ",
    print cooling_off_time[i],
    print ";"

print "def List<Int>  cooling_off_time_list() = list",
print "[%s]" % ",".join([ "cooling_off_time_" + unicode(i) + "()" for i in range(len(cooling_off_time))]),
print ";\n"


# generate initial_instances def
#if not initial_instances:
#    for i in average_times:
#        total_computing_time = i*sum(jobs_per_time_window)
#        total_time = len(jobs_per_time_window) * time_window
#        initial_instances.append( max(1,
#            int(math.ceil(float(total_computing_time)/total_time * 0.5))))
  

for i in range(len(initial_instances)):
    print "def Int initial_instances_" + unicode(i) + "() = ",
    print initial_instances[i],
    print ";"

print "def List<Int> initial_instances_list() = list",
print "[%s]" % ",".join([ "initial_instances_" + unicode(i) + "()" for i in range(len(initial_instances))]),
print ";\n"

# generate instance_cost_list def
costs = average_times
print "def List<Int>  instance_cost_list() = list",
print costs,
print ";\n"            

# generate scaling in and out threshold

for i in range(len(scaling_in)):
    print "def Int scale_in_threshold_" + unicode(i) + "() = ",
    print max(1,int(math.ceil(float(scaling_in[i])/instance_base_speed))),
    print ";"

print "def List<Int>  scale_in_threshold_list() = list",
print "[%s]" % ",".join([ "scale_in_threshold_" + unicode(i) + "()" for i in range(len(scaling_in))]),
print ";\n"

for i in range(len(scaling_out)):
    print "def Int scale_out_threshold_" + unicode(i) + "() = ",
    print max(0,int(math.ceil(float(scaling_out[i])/instance_base_speed))),
    print ";"

print "def List<Int>  scale_out_threshold_list() = list",
print "[%s]" % ",".join([ "scale_out_threshold_" + unicode(i) + "()" for i in range(len(scaling_out))]),
print ";\n"

# generate scaling in and out amounts
for i in range(len(scale_in_amount_list)):
    print "def Int scale_in_amount_" + unicode(i) + "() = ",
    print scale_in_amount_list[i],
    print ";"

print "def List<Int> scale_in_amount_list() = list",
print "[%s]" % ",".join([ "scale_in_amount_" + unicode(i) + "()" for i in range(len(scale_in_amount_list))]),
print ";\n"

for i in range(len(scale_out_amount_list)):
    print "def Int scale_out_amount_" + unicode(i) + "() = ",
    print scale_out_amount_list[i],
    print ";"

print "def List<Int> scale_out_amount_list() = list",
print "[%s]" % ",".join([ "scale_out_amount_" + unicode(i) + "()" for i in range(len(scale_out_amount_list))]),
print ";\n"

# parallel_cost
print "def List<Int> parallel_cost_list() = list",
print parallel_cost,
print ";\n"

# instance_speed
print "def List<Int>  instance_speed_list() = list",
print instance_speed,
print ";\n"

# instance_init_time_list
print "def List<Int>  instance_init_time_list() = list",
print instance_init_time_slots,
print ";\n"

# drop requests x -> probability of keeping is 1/x
# 0 always kept
print "def List<Int>  drop_requests() = list",
print drop_requests,
print ";\n"

#scaling_down_ratio
print "def List<Rat>  scaling_down_ratio_list() = list[",
print ",".join(scaling_down_ratio),
print "];\n"

# max_conn
print "def List<Int>  max_conn_list() = list",
print max_conn,
print ";\n"

# generate jobs_per_time_slot def
jobs_arrival_times = []
counter = 0
for i in jobs_per_time_window:    
        for j in range(i):
            jobs_arrival_times.append(counter + j * time_window * time_scaling_factor / instance_base_speed / i)
        counter += time_window * time_scaling_factor / instance_base_speed


jobs_per_time_slot = {}
for i in range(int(len(jobs_per_time_window)*time_window * time_scaling_factor/instance_base_speed)):
    jobs_per_time_slot[i] = 0
for i in jobs_arrival_times:
    jobs_per_time_slot[int(i)] += 1

ls = [ jobs_per_time_slot[x] for x in sorted(jobs_per_time_slot.keys())]

ELEMENTS_PER_LIST = 100000
counter = 0
if ELEMENTS_PER_LIST < len(ls):
		print "def List<Int> jobs_per_time_slot() = concatenate(list" + unicode(ls[0:ELEMENTS_PER_LIST]) + ",jobs_aux" + unicode(counter) + "());"
		for i in range(1,len(ls)/ELEMENTS_PER_LIST):
				print "def List<Int> jobs_aux" + unicode(counter) + "() = concatenate(list" + unicode(ls[i*ELEMENTS_PER_LIST:(i+1)*ELEMENTS_PER_LIST]) + ",jobs_aux" + unicode(counter+1) + "());"
				counter += 1
		print "def List<Int> jobs_aux" + unicode(counter)  + "() = list" + unicode(ls[(i+1)*ELEMENTS_PER_LIST:]) + ";"
else:
		print "def List<Int> jobs_per_time_slot() = list" + unicode(ls) + ";"
