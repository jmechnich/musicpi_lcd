from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

import dateutil.parser
from   dateutil.tz import tzlocal
import gps

class GPSPrinter(Printer):
    def __init__(self,**kwargs):
        super(GPSPrinter,self).__init__(**kwargs)
        
    def init(self):
        self.lcd.set_cursor(0,0)
        self.lcd.set_color(*self.color)
        self.lcd.message('Opening GPS'.center(self.cols) +'\n' + ' '*self.cols)
        self.update()
        self.active = 0
        self.render(True)
        
    def update(self):
        session = gps.gps(mode=gps.WATCH_ENABLE)
        gpsinfo = None
        maxtries = 10
        try:
            while not gpsinfo and maxtries:
                report = session.next()
                if report['class'] == 'TPV':
                    gpsinfo = dict(report)
                    session.close()
                    break
                maxtries -= 1
        except StopIteration:
            pass
        
        mode = gpsinfo.get('mode', 1)
        self.pages = []
        if mode > 1:
            gpstime   = gpsinfo.get('time', None)
            page = Page()
            page.add( ScrollText("Lon"   + ("%f" % gpsinfo.get('lon', 0.0)).rjust(13), self.cols))
            page.add( ScrollText("Lat"   + ("%f" % gpsinfo.get('lat', 0.0)).rjust(13), self.cols))
            self.pages.append(page)
            page=Page()
            page.add( ScrollText("Speed" + ("%d m/s" % gpsinfo.get('speed', 0)).rjust(11), self.cols))
            page.add( ScrollText("Track" + ("%d deg" % gpsinfo.get('track', 0)).rjust(11), self.cols))
            self.pages.append(page)
            if mode == 3:
                page = Page()
                page.add( ScrollText("Alt" + ("%d m" % gpsinfo.get('alt',0)).rjust(13), self.cols))
                page.add( Text(width=self.cols))
                self.pages.append(page)
            if gpstime:
                page = Page()
                localtime = dateutil.parser.parse(gpstime).astimezone(tzlocal())
                page.add( ScrollText("Time" + ("%s" % localtime.strftime('%H:%M:%S')).rjust(12), self.cols))
                page.add( ScrollText("Date" + ("%s" % localtime.date()).rjust(12), self.cols))
                self.pages.append(page)
        else:
            page = Page()
            page.add( Text("No GPS fix", self.cols))
            self.pages.append(page)
