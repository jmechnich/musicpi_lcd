from threading import Thread, Lock, Event
import logging

class BaseThread(Thread):
    def __init__(self,logger=logging.getLogger()):
        super(BaseThread,self).__init__()
        self.logger = logger
        self._lock  = Lock()
        self._stop  = Event()
        self._data  = None

    def set_data(self,data):
        with self._lock:
            self._data = data

    def add_data(self,data):
        with self._lock:
            if self._data:
                self._data += data
            else:
                self._data = data
    
    def pop_data(self):
        with self._lock:
            old = self._data
            self._data = None
        return old
    
    def data(self):
        with self._lock:
            old = type(self._data)(self._data)
        return old
    
    def iterate(self):
        return not self._stop.is_set()
        
    def stop(self):
        if not self.is_alive():
            self.logger.debug("%s: Thread not running" % type(self).__name__)
            return
        self.logger.debug("%s: Stopping thread" % type(self).__name__)
        self._stop.set()
        self.stop_iterate()
        self.join()
        self.logger.debug("%s: Thread stopped" % type(self).__name__)
    
    def stop_iterate(self):
        pass
        

    def sleep(self, time):
        return self._stop.wait(time)
