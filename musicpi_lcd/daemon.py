import errno, os, sys, logging, psutil

def detach():
    stdin  = '/dev/null'
    stdout = '/dev/null'
    stderr = '/dev/null'
    
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)
        
    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)
       
    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

def check_if_root():
    return os.geteuid() == 0

def check_if_running(name, kill=False):
    if check_if_root():
        pidfile = "/var/run/%s.pid" % name
    else:
        pidfile = os.path.join(os.environ['HOME'],".%s.pid" % name)
    if not os.path.exists( pidfile):
        return False
    f = open(pidfile)
    oldpid = int(f.readline().strip())
    f.close()

    cmdlinefile = os.path.join('/proc',str(oldpid),'cmdline')
    if not os.path.exists( cmdlinefile):
        return False
    f = open(cmdlinefile)
    args = f.readline().strip().split('\0')
    f.close()
    if len(args) > 1 and not args[0].endswith(name):
        if not args[1].endswith(name):
            return False

    if kill:
        try:
            import signal, time
            print "Sending SIGTERM to", oldpid
            os.kill(oldpid, signal.SIGTERM)
            maxwait = 5
            while maxwait:
                if not psutil.pid_exists(oldpid):
                    return False
                print "Sleeping for 1s"
                time.sleep(1)
                maxwait -= 1
            print "Sending SIGKILL to", oldpid
            os.kill(oldpid, signal.SIGKILL)
            maxwait = 5
            while maxwait:
                if not psutil.pid_exists(oldpid):
                    return False
                print "Sleeping for 1s"
                time.sleep(1)
                maxwait -= 1
            return True
        except:
            raise
    
    return True
    
def create_pid_file(name):
    if check_if_root():
        pidfile = '/var/run/%s.pid' % name 
    else:
        pidfile = os.path.join(os.environ['HOME'],".%s.pid" % name)
    f = open(pidfile, 'w')
    print>>f, os.getpid()
    f.close()
    import atexit
    atexit.register(lambda: os.path.exists(pidfile) and os.remove(pidfile))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def create_logger(name,logfile=None):
    # create logger for 'name'
    logger = None
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    logger = logging.getLogger(name)

    # logging to console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    
    # logging to file
    if logfile:
        mkdir_p(os.path.dirname(logfile))
        fileHandler = logging.FileHandler(logfile)
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
        logger.debug('Logging to %s' % logfile)
    
    # redirect stdout and stderr to logger
    class LoggerWriter:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level

        def write(self, message):
            if message != '\n':
                self.logger.log(self.level, message)
    lw = LoggerWriter(logger, logging.WARNING)
    sys.stdout = lw
    sys.stderr = lw
    
    return logger
