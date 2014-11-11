from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

from threading import Lock, Thread, Event

import dateutil.parser
from   dateutil.tz import tzlocal

import gps, time

class GPSThread(Thread):
    def __init__(self,parent):
        super(GPSThread,self).__init__()
        self._parent  = parent
        self._lock    = Lock()
        self._stop    = Event()
        self._gpsinfo = {}
        
    def run(self):
        self._stop.clear()
        session = gps.gps(mode=gps.WATCH_ENABLE)
        while not self._stop.is_set():
            gpsinfo = None
            maxtries = 10
            try:
                while not gpsinfo and maxtries:
                    report = session.next()
                    if report['class'] == 'TPV':
                        gpsinfo = dict(report)
                        break
                    maxtries -= 1
            except StopIteration:
                pass
            if gpsinfo:
                self.set_gpsinfo(gpsinfo)
            if self._stop.wait(1):
                break
        session.close()

    def stop(self):
        self._stop.set()

    def get_gpsinfo(self):
        with self._lock:
            ret = dict(self._gpsinfo)
        return ret
    
    def set_gpsinfo(self, gpsinfo={}):
        with self._lock:
            old = dict(self._gpsinfo)
            self._gpsinfo = gpsinfo
        return old

class GPSPrinter(Printer):
    PAGE_POS, PAGE_SPEED, PAGE_ALT, PAGE_TIME = xrange(4)
    
    def __init__(self,**kwargs):
        super(GPSPrinter,self).__init__(**kwargs)
        
        # internal variables
        self._thread = None
        
    def init_layout(self):
        super(GPSPrinter,self).init_layout()

        page = Page(self.lcd,idx=self.PAGE_POS)
        self.lon = page.add_scroll_line(header="Lon")
        self.lat = page.add_scroll_line(header="Lat")
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE_SPEED)
        self.speed = page.add_scroll_line(header="Speed")
        self.track = page.add_scroll_line(header="Track")
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE_ALT)
        self.alt = page.add_scroll_line(header="Alt")
        page.add_line(Text(width=self.cols))
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE_TIME)
        self.time = page.add_scroll_line(header="Time")
        self.date = page.add_scroll_line(header="Date")
        self.pages.append(page)
        
        self.active = self.PAGE_POS

    def __del__(self):
        self.stop()
    
    def stop(self):
        if not self._thread:
            return
        if not self._thread.is_alive():
            if self.debug: print type(self).__name__, ": Thread not running"
        if self.debug: print type(self).__name__, ": Stopping thread"
        self._thread.stop()
        self._thread.join()
        self._thread = None
        if self.debug: print type(self).__name__, ": Thread stopped"
        
    def init(self):
        if not self._thread:
            self._thread = GPSThread(self)
            self._thread.start()
        self.update()
        self.lcd.set_color(*self.color)
        self.render(True)
        
    def render(self,force=True):
        self.update()
        super(GPSPrinter,self).render(force)
    
    def update(self):
        if self.debug: print type(self).__name__, 'updating'
        gpsinfo = self._thread.get_gpsinfo()
        if not len(gpsinfo):
            return
        mode = gpsinfo.get('mode', 1)
        if mode > 1:
            gpstime = gpsinfo.get('time', None)
            self.lon.setText(("%f" % gpsinfo.get('lon', 0.0)).rjust(self.lon.width))
            self.lat.setText(("%f" % gpsinfo.get('lat', 0.0)).rjust(self.lat.width))
            self.speed.setText(("%d m/s" % gpsinfo.get('speed', 0)).rjust(self.speed.width))
            self.track.setText(("%d deg" % gpsinfo.get('track', 0)).rjust(self.track.width))
            if mode == 3:
                self.alt.setText(("%d m" % gpsinfo.get('alt',0)).rjust(self.alt.width))
            if gpstime:
                localtime = dateutil.parser.parse(gpstime).astimezone(tzlocal())
                self.time.setText(("%s" % localtime.strftime('%H:%M:%S')).rjust(self.time.width))
                self.date.setText(("%s" % localtime.date()).rjust(self.date.width))
