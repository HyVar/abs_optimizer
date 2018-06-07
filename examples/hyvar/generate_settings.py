import math

# the instance speed in ms for a timeslot
instance_base_speed = 1000

# speed consumption in ms after which instances may switch jobs
switch_time_slot = 250

# average times in ms for all the components.
# component list:
#   encoder
#   hyvarrec
#   decoder
#   variant
#   code
#   c compiler
#   java compiler

names = [
  'encoder',
  'hyvarrec',
  'decoder',
  'resolution_spl',
#  'resolution_conf',
  'variant_gen',
  'code_gen',
  'c_compiler',
  'java_compiler']

# average time of every component in ms
avg_times = [instance_base_speed]*len(names)
avg_times[names.index('encoder')] = 365
avg_times[names.index('hyvarrec')] = 1033
avg_times[names.index('decoder')] = 343
avg_times[names.index('resolution_spl')] = 247
#avg_times[names.index('resolution_conf')] = 340
avg_times[names.index('variant_gen')] = 666
avg_times[names.index('code_gen')] = 7769
avg_times[names.index('c_compiler')] = 23268
avg_times[names.index('java_compiler')] = 14237

# init time for instances in ms
instance_init_times = [240*1000]*len(names)
#instance_init_times[names.index('hyvarrec')] = (33 + 420)*1000
#instance_init_times[names.index('c_compiler')] = (32 + 349)*1000

# number of jobs submitted every time window of 15 minutes
# traffic pattern is derived from the website data.gov.uk
# listing the number of cars registered on the A414 highway
# on Monday,March 2, 2015
# every time windows is equivalent to x milliseconds
time_window = 15 * 60 * 1000
jobs_per_time_window =  [19,19,16,13,12,11,10,10,10,9,11,10,19,16,18,15,15,20,38,36,
    46,73,103,95,107,139,198,221,265,270,287,326,334,326,304,259,
    251,231,221,191,172,174,171,161,163,162,169,158,156,173,
    169,166,167,174,170,165,167,163,180,179,186,177,203,193,
    234,246,251,235,262,280,276,267,253,220,201,166,151,137,
    126,105,90,93,76,67,74,75,68,64,71,65,50,42,40,31,28,27,]
jobs_per_time_window = [1*x for x in jobs_per_time_window]

# if components are more powerful specify them here
# useful when more components are merged into one
instance_speed = [instance_base_speed] * len(names)

# checking_avg_time_interval (final result in time slots)
checking_avg_time_interval = int(math.ceil(float(60) * 1000 / instance_base_speed))

# cooling off in ms (multiple of checking_avg_time_interval)
cooling_off_time = [300] * len(names)
cooling_off_time[names.index('encoder')] = 300
cooling_off_time[names.index('hyvarrec')] = 300
cooling_off_time[names.index('decoder')] = 300
cooling_off_time[names.index('resolution_spl')] = 300
#cooling_off_time[names.index('resolution_conf')] = 300
cooling_off_time[names.index('variant_gen')] = 300
cooling_off_time[names.index('code_gen')] = 300
cooling_off_time[names.index('c_compiler')] = 300
cooling_off_time[names.index('java_compiler')] = 300

cooling_off_time = [x * int(math.ceil(float(1000) / instance_base_speed)) for x in cooling_off_time]

# initial instances per component
initial_instances = [1] * len(names)
#initial_instances = [1,2,1,1,13]

# x scale in factor in ms
scaling_in = [ 3*x for x in avg_times]

scaling_in[names.index('encoder')] = 438
scaling_in[names.index('hyvarrec')] = 1240
scaling_in[names.index('decoder')] = 411
scaling_in[names.index('resolution_spl')] = 296
#scaling_in[names.index('resolution_conf')] = 504
scaling_in[names.index('variant_gen')] = 799
scaling_in[names.index('code_gen')] = 9322
scaling_in[names.index('c_compiler')] = 27291
scaling_in[names.index('java_compiler')] = 17084

scaling_in = [max(x,instance_base_speed) for x in scaling_in]

# x scale out factor in ms
scaling_out_diff = [ x for x in avg_times]

scaling_out_diff[names.index('encoder')] = 1095
scaling_out_diff[names.index('hyvarrec')] = 3099
scaling_out_diff[names.index('decoder')] = 1029
scaling_out_diff[names.index('resolution_spl')] = 741
#scaling_out_diff[names.index('resolution_conf')] = 756
scaling_out_diff[names.index('variant_gen')] = 1998
scaling_out_diff[names.index('code_gen')] = 23307
scaling_out_diff[names.index('c_compiler')] = 69804
scaling_out_diff[names.index('java_compiler')] = 42711

# amount of instance to increase every scale in
scale_in_amount_list = [1] * len(names)

scale_in_amount_list[names.index('encoder')] = 1
scale_in_amount_list[names.index('hyvarrec')] = 1
scale_in_amount_list[names.index('decoder')] = 1
scale_in_amount_list[names.index('resolution_spl')] = 1
#scale_in_amount_list[names.index('resolution_conf')] = 1
scale_in_amount_list[names.index('variant_gen')] = 1
scale_in_amount_list[names.index('code_gen')] = 1
scale_in_amount_list[names.index('c_compiler')] = 1
scale_in_amount_list[names.index('java_compiler')] = 1

# amount of instance to decrease every scale out
scale_out_amount_list = [1] * len(names)

scale_out_amount_list[names.index('encoder')] = 2
scale_out_amount_list[names.index('hyvarrec')] = 2
scale_out_amount_list[names.index('decoder')] = 2
scale_out_amount_list[names.index('resolution_spl')] = 2
#scale_out_amount_list[names.index('resolution_conf')] = 1
scale_out_amount_list[names.index('variant_gen')] = 2
scale_out_amount_list[names.index('code_gen')] = 2
scale_out_amount_list[names.index('c_compiler')] = 2
scale_out_amount_list[names.index('java_compiler')] = 2

# drop requests x-> discard x and keep the x + 1
drop_requests = [0] * len(names)

#scaling_down_ratio (RAT)
# pending_jobs <  size(keys(instances)) * scaling_down_ratio
# allows the scaling down
scaling_down_ratio = [unicode(int(float(60000)/x)*10) + "/10" for x in avg_times]
#scaling_down_ratio[names.index('hyvarrec')] = "25"
#scaling_down_ratio[names.index('code_gen')] = "15/10"
#scaling_down_ratio[names.index('c_compiler')] = "15/10"
#scaling_down_ratio[names.index('java_compiler')] = "15/10"

#max_conn (0 means infinite) 
max_conn = [0]*len(names)
max_conn[names.index('encoder')] = 100
max_conn[names.index('hyvarrec')] = 100
max_conn[names.index('decoder')] = 100
max_conn[names.index('resolution_spl')] = 100
#max_conn[names.index('resolution_conf')] = 100
max_conn[names.index('variant_gen')] = 25
max_conn[names.index('code_gen')] = 9
max_conn[names.index('c_compiler')] = 6
max_conn[names.index('java_compiler')] = 7

# parallel_part
parallel_cost = [0] * len(names)

print "module Settings;"
print "export *;\n" 

print "def Int instance_base_speed() = ",
print instance_base_speed,
print ";\n"

# switch_time_slot
print "def Int switch_time_slot() = ",
print switch_time_slot,
print ";\n"

# checking_avg_time_interval (in time slots)
print "def List<String> component_name_list() = list",
print '["{}"];\n'.format('","'.join(names))

# checking_avg_time_interval (in time slots)
print "def Int checking_avg_time_interval() = ",
print checking_avg_time_interval,
print ";\n"

# cooling_off_time
for i in range(len(cooling_off_time)):
    print "def Int cooling_off_time_" + names[i] + "() = ",
    print cooling_off_time[i],
    print ";"

print "def List<Int>  cooling_off_time_list() = list",
print "[%s]" % ",".join([ "cooling_off_time_" + names[i] + "()" for i in range(len(cooling_off_time))]),
print ";\n"

for i in range(len(initial_instances)):
    print "def Int initial_instances_" + names[i] + "() = ",
    print initial_instances[i],
    print ";"

print "def List<Int> initial_instances_list() = list",
print "[%s]" % ",".join([ "initial_instances_" + names[i] + "()" for i in range(len(initial_instances))]),
print ";\n"

# generate instance_cost_list def
costs = avg_times
print "def List<Int>  instance_cost_list() = list",
print costs,
print ";\n"            

# generate scaling in and out threshold

for i in range(len(scaling_in)):
    print "def Int scale_in_threshold_" + names[i] + "() = ",
    print max(1,int(math.ceil(float(scaling_in[i])/instance_base_speed))),
    print ";"

print "def List<Int>  scale_in_threshold_list() = list",
print "[%s]" % ",".join([ "scale_in_threshold_" + names[i] + "()" for i in range(len(scaling_in))]),
print ";\n"

for i in range(len(scaling_out_diff)):
    print "def Int scale_out_threshold_diff_" + names[i] + "() = ",
    print max(0,int(math.ceil(float(scaling_out_diff[i])/instance_base_speed))),
    print ";"

print "def List<Int>  scale_out_threshold_diff_list() = list",
print "[%s]" % ",".join([ "scale_out_threshold_diff_" + names[i] + "()" for i in range(len(scaling_out_diff))]),
print ";\n"

# generate scaling in and out amounts
for i in range(len(scale_in_amount_list)):
    print "def Int scale_in_amount_" + names[i] + "() = ",
    print scale_in_amount_list[i],
    print ";"

print "def List<Int> scale_in_amount_list() = list",
print "[%s]" % ",".join([ "scale_in_amount_" + names[i] + "()" for i in range(len(scale_in_amount_list))]),
print ";\n"

for i in range(len(scale_out_amount_list)):
    print "def Int scale_out_amount_" + names[i] + "() = ",
    print scale_out_amount_list[i],
    print ";"

print "def List<Int> scale_out_amount_list() = list",
print "[%s]" % ",".join([ "scale_out_amount_" + names[i] + "()" for i in range(len(scale_out_amount_list))]),
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
instance_init_time_slots = [ int(math.ceil(float(x) / instance_base_speed)) for x in instance_init_times]
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
            jobs_arrival_times.append(counter + float(j) * time_window / i)
        counter += time_window


max_val = instance_base_speed
ls = [0]
while jobs_arrival_times:
    if jobs_arrival_times[0] > max_val:
      ls.append(0)
      max_val += instance_base_speed
    else:
      ls[-1] += 1
      jobs_arrival_times.pop(0) 

ELEMENTS_PER_LIST = 10000
counter = 0
if ELEMENTS_PER_LIST < len(ls):
    print "def List<Int> jobs_per_time_slot() = concatenate(list" + unicode(ls[0:ELEMENTS_PER_LIST]) + ",jobs_aux" + unicode(counter) + "());"
    for i in range(1,len(ls)/ELEMENTS_PER_LIST):
        print "def List<Int> jobs_aux" + unicode(counter) + "() = concatenate(list" + unicode(ls[i*ELEMENTS_PER_LIST:(i+1)*ELEMENTS_PER_LIST]) + ",jobs_aux" + unicode(counter+1) + "());"
        counter += 1
    print "def List<Int> jobs_aux" + unicode(counter)  + "() = list" + unicode(ls[(i+1)*ELEMENTS_PER_LIST:]) + ";"
else:
    print "def List<Int> jobs_per_time_slot() = list" + unicode(ls) + ";"
