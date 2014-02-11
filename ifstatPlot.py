# ifstatPlot.py
# simple wrapper to process ifstat and graph the data to a chart
#
#
# This is a basic network monitoring tool written in python utilizing ifstat.
# It uses matplotlib in conjunction with ifstat to plot real network data.
#
#
from __future__ import print_function
from subprocess import PIPE, Popen
from threading  import Thread
import matplotlib.pyplot as plt
import getopt, sys
#matplotlib.use('Agg')

plt.ion()                           # interaction mode needs to be turned off

try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
	for line in iter(out.readline, b''):
		line = line.decode(sys.stdout.encoding)
		queue.put(line)
	out.close()

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hi:T",["help","interface=","total"])
	except getopt.GetoptError, err:
		print(str(err))
		sys.exit()
		
	interface = False
	totalBw	  = False
	
	for o, a in opts:
		if o in ("-h", "--help"):
			print("Usage: "+sys.argv[0]+" [options]")
			print("---- Options ----")
			print("   -h  --help                  This help menu")
			print("                               ")
			print("   -i  --interface=eth0,tun0   Specify list of interfaces to monitor")
			print("                               seperated by commas")
			print("   -T  --total                 Report total bandwidth for all")
			print("                               monitored interfaces")
			sys.exit()
		elif o in ("-i", "--interface"):
			interface = a
		elif o in ("-T", "--total"):
			totalBw = True
	
	cmdIfstat = ['ifstat', '-n']
	if interface:
		cmdIfstat.append('-i')
		cmdIfstat.append(interface)		# append the list of interfaces to command line
	
	if totalBw:
		cmdIfstat.append('-T')			# append total switch to command line
	
	p = Popen(cmdIfstat, stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
	q = Queue()
	t = Thread(target=enqueue_output, args=(p.stdout, q))
	t.daemon = True # thread dies with the program
	t.start()
	
	# initially the queue is empty and stdout is open
	# stdout is closed when enqueue_output finishes
	# then continue printing until the queue is empty 

	cntStart			= 0
	cntrInter			= 0
	arrTotalBandwidth	= []
	arrInterBandwidth	= []
	arrInterface		= []
	while not p.stdout.closed or not q.empty():
		try:
			line = q.get_nowait()
		except Empty:
			continue
		else:
			lineSplit = line.split()
			if cntStart == 0: 					# first loop through, collect all interfaces
				cntInterfaces = len(lineSplit)	# total number of interfaces
				interfaces = lineSplit				
				if totalBw:
					totalIn  = (cntInterfaces * 2) - 2
					#totalOut = (cntInterfaces * 2) - 1
				if interface:
					interf = interface.split(',')
					for inter in interf:
						for interfa in interfaces:
							if inter == interfa:	# loop through both interface list, when equal save offset
								arrInterface.append({cntrInter:inter})	# array of dictionaries of interfaces
								arrInterBandwidth.append([u'0.0'])			# plus offset; populate dummy list
						cntrInter += 1									
				cntStart = 1
				continue
			
			if lineSplit[0] != 'KB/s':			# discard header
				plt.clf()
				plt.xlabel('Bandwidth Usage', fontsize=14, color='black')
				plt.ylabel('KB/s out', color='blue')
				if totalBw:
					arrBandwidth.append(lineSplit[totalIn])
					plt.plot(arrBandwidth, label='Total')
					#plt.draw()
				
				cntrInter	= 0
				if interface:
					for inter in arrInterface:
						#arrTmp = arrInterBandwidth[cntrInter]
						offsetIn  = ((cntrInter + 1) * 2 ) - 2
						#offsetOut = ((cntrInter + 1) * 2 ) - 1
						
						if lineSplit[offsetIn] == 'n/a':
							arrInterBandwidth[cntrInter].append(u'0.0')
						else:
							arrInterBandwidth[cntrInter].append(lineSplit[offsetIn])
						#print(inter[cntrInter])
						plt.plot(arrInterBandwidth[cntrInter], label=inter[cntrInter])
						plt.legend(loc='upper left', fancybox=True, shadow=True, prop=dict(size=10))
						cntrInter += 1
					#print(arrInterBandwidth)
				plt.draw()
				
	return 0

if __name__ == '__main__':
	main()