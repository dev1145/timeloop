
#from timeloop.exceptions import ServiceExit
#from timeloop.job import Job
#from timeloop.helpers import service_shutdown


from threading import Thread, Event
from datetime import timedelta

import logging
import sys
import signal
import time

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def service_shutdown(signum, frame):
    raise ServiceExit
    
class Job(Thread):
    def __init__(self, interval, execute, *args, allow_drift=False, initial_launch=False, max_run_times=None, **kwargs):
        Thread.__init__(self)
        self.stopped = Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs
        self.allow_drift= allow_drift
        self.max_run_times= max_run_times
        self.initial_launch= initial_launch
        
    def stop(self):
        self.stopped.set()
        #self.join()

    def run(self):
        if type(self.max_run_times)==int and self.max_run_times <= 0 : 
            return
        next_wait_sec = self.interval.total_seconds()
        next_time_point_sec = time.time() + self.interval.total_seconds()
        while (self.initial_launch and (self.max_run_times==None or type(self.max_run_times)==int and self.max_run_times > 0 )
               or not self.stopped.wait(next_wait_sec)):
            self.execute(*self.args, **self.kwargs)
            
            if self.initial_launch : self.initial_launch = False
            
            self.max_run_times = self.max_run_times -1 if type(self.max_run_times)==int else None
            if type(self.max_run_times)==int and self.max_run_times <= 0 : break
            
            if self.allow_drift:
                next_wait_sec = self.interval.total_seconds()
            else: 
                next_time_point_sec += self.interval.total_seconds()
                next_wait_sec = next_time_point_sec - time.time() 
                
            
class Timeloop():
    def __init__(self, add_logger=False):
        '''
        add_looger = False/True/Name/logging.Logger/logging.RootLogger
        '''
        self.jobs = []
        if add_logger :
            if type(add_logger) == logging.Logger or type(add_logger) == logging.RootLogger:
                logger=add_logger
            else :
                logger = logging.getLogger('timeloop' if type(add_logger) != str else add_logger)
            if not(logger.handlers or logger.hasHandlers() ): #hasHandlers check logging hierarcy by dot(.)
                ch = logging.StreamHandler(sys.stdout)
                ch.setLevel(logging.INFO)
                formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
                ch.setFormatter(formatter)
                logger.addHandler(ch)
                logger.setLevel(logging.INFO)
            self.logger = logger
        else:
            self.logger = lambda : None
            self.logger.info = lambda *args, **kwargs : None

    def _add_job(self, func, interval, *args, **kwargs):
        j = Job(interval, func, *args, **kwargs)
        self.jobs.append(j)

    def _block_main_thread(self):
        signal.signal(signal.SIGTERM, service_shutdown)
        signal.signal(signal.SIGINT, service_shutdown)

        while True:
            try:
                alive_jobs=self._join_jobs(0.001)
                self.logger.log(logging.INFO-1 , "alive_josbs=%s", alive_jobs)
                if alive_jobs==0 : break
                time.sleep(1)
                
            except ServiceExit:
                self.stop()
                break

    def _start_jobs(self, block):
        for j in self.jobs:
            j.daemon = not block
            j.start()
            self.logger.info("Registered job {}".format(j.execute))

    def _stop_jobs(self):
        for j in self.jobs:
            self.logger.info("Stopping job {}".format(j.execute))
            j.stop()
        self._join_jobs()
        
    def _join_jobs(self, join_timeout=None):
        for j in self.jobs:
            j.join(join_timeout)
        return sum([1 for j in self.jobs if j.is_alive()] )

    def job(self, interval, allow_drift=False, initial_launch=False, max_run_times=None):
        def decorator(f):
            self._add_job(f, interval, allow_drift=allow_drift, initial_launch=initial_launch, max_run_times=max_run_times)
            return f
        return decorator

    def stop(self):
        self._stop_jobs()
        self.logger.info("Timeloop exited.")

    def start(self, block=False):
        self.logger.info("Starting Timeloop..")
        self._start_jobs(block=block)

        self.logger.info("Timeloop now started. Jobs will run based on the interval set")
        if block:
            self._block_main_thread()            
