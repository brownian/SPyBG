#
#
#

import sys, os, signal

'''This module is used to fork the current process into a daemon.
	Almost none of this is necessary (or advisable) if your daemon 
	is being started by inetd. In that case, stdin, stdout and stderr are 
	all set up for you to refer to the network connection, and the fork()s 
	and session manipulation should not be done (to avoid confusing inetd). 
	Only the chdir() and umask() steps remain as useful.
	References:
		UNIX Programming FAQ
			1.7 How do I get my program to act like a daemon?
				http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
	
		Advanced Programming in the Unix Environment
			W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.
	'''

def deamonize (
		dir='/',
		stdout='/dev/null', stderr=None, stdin='/dev/null',
		pidfile=None, startmsg = 'started with pid %s' ):
	'''
		This forks the current process into a daemon.
		The stdin, stdout, and stderr arguments are file names that
		will be opened and be used to replace the standard file descriptors
		in sys.stdin, sys.stdout, and sys.stderr.
		These arguments are optional and default to /dev/null.
		Note that stderr is opened unbuffered, so
		if it shares a file with stdout then interleaved output
		may not appear in the order that you expect.
	'''
	# Do first fork.
	try: 
		pid = os.fork() 
		if pid > 0: sys.exit(0) # Exit first parent.
	except OSError, e: 
		sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
		sys.exit(1)
		
	# Decouple from parent environment.
	os.chdir(dir) 
	os.umask(0) 
	os.setsid() 
	
	# Do second fork.
	try: 
		pid = os.fork() 
		if pid > 0: sys.exit(0) # Exit second parent.
	except OSError, e: 
		sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
		sys.exit(1)
	
	# Open file descriptors and print start message
	if not stderr: stderr = stdout
	si = file(stdin, 'r')
	so = file(stdout, 'a+')
	se = file(stderr, 'a+', 0)
	pid = str(os.getpid())
	sys.stderr.write("\n%s\n" % startmsg % pid)
	sys.stderr.flush()
	if pidfile: file(pidfile,'w+').write("%s\n" % pid)
	
	# Redirect standard file descriptors.
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())



def startstop ( 
		dir='/',
		stdout='/dev/null', stderr=None, stdin='/dev/null',
		pidfile='pid.txt', startmsg = 'started with pid %s', action='start' ):
	if action:
		try:
			pf	= file(pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
		 
		if 'stop' == action or 'restart' == action:
			if not pid:
				mess = "Could not stop, pid file '%s' missing.\n"
				sys.stderr.write(mess % pidfile)
				if 'stop' == action:
					sys.exit(1)
				action = 'start'
				pid = None
			else:
			   try:
				  while 1:
					  os.kill ( pid, signal.SIGTERM )
					  time.sleep(1)
			   except OSError, err:
				  err = str(err)
				  if err.find("No such process") > 0:
					  os.remove(pidfile)
					  if 'stop' == action:
						  sys.exit(0)
					  action = 'start'
					  pid = None
				  else:
					  print str(err)
					  sys.exit(1)
		
		if 'start' == action:
			if pid:
				mess = "Start aborted since pid file '%s' exists.\n"
				sys.stderr.write(mess % pidfile)
				sys.exit(1)

			deamonize ( dir, stdout, stderr, stdin, pidfile, startmsg )
			return

		if 'status' == action:
			if not pid:
				sys.stderr.write('Status: Stopped\n')

			else: sys.stderr.write('Status: Running\n')
			sys.exit(0)

