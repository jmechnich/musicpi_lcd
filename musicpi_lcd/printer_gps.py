from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

from threading import Lock, Thread

import dateutil.parser
from   dateutil.tz import tzlocal

import gps, time

class GPSThread(Thread):
    def __init__(self,parent):
        super(GPSThread,self).__init__()
        self.parent = parent
        
    def run(self):
        self.do_iterate = True
        session = gps.gps(mode=gps.WATCH_ENABLE)
        while self.do_iterate:
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
                self.parent.set_gpsinfo(gpsinfo)
            time.sleep(1)
        session.close()
        
class GPSPrinter(Printer):
    def __init__(self,**kwargs):
        super(GPSPrinter,self).__init__(**kwargs)
        self.active = 0
        self.gpsinfo = {}
        self.init_page()
        self.thread = GPSThread(self)
        self.lock = Lock()
        self.thread.start()
        
    def stop(self):
        self.thread.do_iterate = False
        self.thread.join()
        
    def init_page(self):
        self.pages = []
        page = Page()
        self.lon = ScrollText()
        page.add_line(self.lon, header="Lon")
        self.lat = ScrollText()
        page.add_line(self.lat, header="Lat")
        self.pages.append(page)

        page = Page()
        self.speed = ScrollText()
        page.add_line(self.speed, header="Speed")
        self.track = ScrollText()
        page.add_line(self.track, header="Track")
        self.pages.append(page)

        page = Page()
        self.alt = ScrollText()
        page.add_line(self.alt, header="Alt")
        page.add_line(Text(width=self.cols))
        self.pages.append(page)

        page = Page()
        self.time = ScrollText()
        page.add_line(self.time, header="Time")
        self.date = ScrollText()
        page.add_line(self.date, header="Date")
        self.pages.append(page)

    def init(self):
        self.update()
        self.lcd.set_color(*self.color)
        self.render(True)
        
    def get_gpsinfo(self):
        self.lock.acquire()
        ret = dict(self.gpsinfo)
        self.lock.release()
        return ret
    
    def set_gpsinfo(self, gpsinfo={}):
        self.lock.acquire()
        old = dict(self.gpsinfo)
        self.gpsinfo = gpsinfo
        self.lock.release()
        return old

    def render(self,force=True):
        self.update()
        super(GPSPrinter,self).render(force=True)
    
    def update(self):
        gpsinfo = self.set_gpsinfo()
        if not len(gpsinfo):
            return
        mode = gpsinfo.get('mode', 1)
        if mode > 1:
            gpstime   = gpsinfo.get('time', None)
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
