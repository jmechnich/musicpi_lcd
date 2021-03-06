from printer import Printer
from text    import *
from thread  import BaseThread as Thread

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
            satellites = None
            maxtries = 10
            try:
                while not gpsinfo and maxtries:
                    report = session.next()
                    if report['class'] == 'TPV':
                        gpsinfo = dict(report)
                        gpsinfo['satellites'] = satellites
                        break
                    elif report['class'] == 'SKY':
                        sats_used  = len([ s for s in report.get('satellites', {}) if s['used'] == True])
                        sats_avail = len([ s for s in report.get('satellites', {})])
                        satellites = (sats_used, sats_avail)
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
        self.PAGES = ['POS', 'SPEED', 'TRACK', 'TIME' ]
        super(GPSPrinter,self).__init__(**kwargs)
        
        # always show GPS printer
        self.timeout_override = True
        
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
        self.alt   = page.add_scroll_line(header="Alt")
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.TRACK)
        self.track = page.add_scroll_line(header="Track")
        self.sat   = page.add_scroll_line(header="Sats used")
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
        self.lon.setText(  ("%f"        %  gpsinfo.get('lon', 0.0)     ).rjust(self.lon.width))
        self.lat.setText(  ("%f"        %  gpsinfo.get('lat', 0.0)     ).rjust(self.lat.width))
        self.speed.setText(("%.1f km/h" % (gpsinfo.get('speed', 0)*3.6)).rjust(self.speed.width))
        self.track.setText(("%d deg"    %  gpsinfo.get('track', 0)     ).rjust(self.track.width))
        self.alt.setText(  ("%d m"      %  gpsinfo.get('alt',   0)     ).rjust(self.alt.width))
        satellites = gpsinfo['satellites']
        if satellites:
            self.sat.setText(("%d/%d" %  satellites).rjust(self.sat.width))
        if gpstime:
            localtime = dateutil.parser.parse(gpstime).astimezone(tzlocal())
            self.time.setText(("%s" % localtime.strftime('%H:%M:%S')).rjust(self.time.width))
            self.date.setText(("%s" % localtime.date()).rjust(self.date.width))
