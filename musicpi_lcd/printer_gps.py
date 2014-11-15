from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *
from musicpi_lcd.thread  import BaseThread as Thread

import dateutil.parser
from   dateutil.tz import tzlocal

import gps, time

class GPSThread(Thread):
    def __init__(self,logger):
        super(GPSThread,self).__init__(logger)
        
    def run(self):
        session = gps.gps(mode=gps.WATCH_ENABLE)
        while self.iterate():
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
                self.set_data(gpsinfo)
            if self.sleep(1):
                break
        session.close()
        
class GPSPrinter(Printer):
    def __init__(self,**kwargs):
        self.PAGES = ['POS', 'SPEED', 'ALT', 'TIME' ]
        super(GPSPrinter,self).__init__(**kwargs)
        
        # internal variables
        self._thread = None
        
    def init_layout(self):
        super(GPSPrinter,self).init_layout()

        page = Page(self.lcd,idx=self.PAGE.POS)
        self.lon = page.add_scroll_line(header="Lon")
        self.lat = page.add_scroll_line(header="Lat")
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.SPEED)
        self.speed = page.add_scroll_line(header="Speed")
        self.track = page.add_scroll_line(header="Track")
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.ALT)
        self.alt = page.add_scroll_line(header="Alt")
        page.add_line(Text(width=self.cols))
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.TIME)
        self.time = page.add_scroll_line(header="Time")
        self.date = page.add_scroll_line(header="Date")
        self.pages.append(page)
        
        self.set_active(self.PAGE.POS)

    def __del__(self):
        self.stop()
    
    def stop(self):
        if not self._thread:
            return
        self._thread.stop()
        
    def init(self):
        if not self._thread:
            self._thread = GPSThread(self.logger)
            self._thread.start()
        self.update()
        self.lcd.set_color(*self.color)
        self.render(True)
        
    def render(self,force=False):
        self.update()
        super(GPSPrinter,self).render(force)
    
    def update(self):
        gpsinfo = self._thread.pop_data()
        if not gpsinfo:
            return
        self.logger.debug( '%s updating' % type(self).__name__)
        mode = gpsinfo.get('mode', 1)
        if mode < 2:
            return
        gpstime = gpsinfo.get('time', None)
        if self.active == self.PAGE.POS:
            self.lon.setText(("%f" % gpsinfo.get('lon', 0.0)).rjust(self.lon.width))
            self.lat.setText(("%f" % gpsinfo.get('lat', 0.0)).rjust(self.lat.width))
        elif self.active == self.PAGE.SPEED:
            self.speed.setText(("%d m/s" % gpsinfo.get('speed', 0)).rjust(self.speed.width))
            self.track.setText(("%d deg" % gpsinfo.get('track', 0)).rjust(self.track.width))
        elif self.active == self.PAGE.ALT and mode == 3:
            self.alt.setText(("%d m" % gpsinfo.get('alt',0)).rjust(self.alt.width))
        elif self.active == self.PAGE.TIME and gpstime:
            localtime = dateutil.parser.parse(gpstime).astimezone(tzlocal())
            self.time.setText(("%s" % localtime.strftime('%H:%M:%S')).rjust(self.time.width))
            self.date.setText(("%s" % localtime.date()).rjust(self.date.width))
