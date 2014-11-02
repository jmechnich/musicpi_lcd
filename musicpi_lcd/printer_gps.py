from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import ScrollText
from musicpi_lcd.util    import colors

import dateutil.parser
from   dateutil.tz import tzlocal
import gps

class GPSPrinter(Printer):
    def __init__(self,**kwargs):
        super(GPSPrinter,self).__init__(**kwargs)
        
    def init(self):
        self.lcd.set_color(*colors['blue'])
        self.lcd.set_cursor(0,0)
        self.lcd.message('Opening GPS'.center(self.cols) +'\n' + ' '*self.cols)
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
        if mode > 1:
            gpstime   = gpsinfo.get('time', None)
            self.rowtext = [
                ScrollText("Lon"   + ("%f" % gpsinfo['lon']).rjust(13), self.cols),
                ScrollText("Lat"   + ("%f" % gpsinfo['lat']).rjust(13), self.cols),
                ScrollText("Speed" + ("%d km/h" % gpsinfo['speed']).rjust(11), self.cols),
                ScrollText("Track" + ("%d deg" % gpsinfo['track']).rjust(11), self.cols),
                ]
            if mode == 3:
                self.rowtext += [ScrollText("Alt"   + ("%d m" % gpsinfo['alt']).rjust(13), self.cols)]
            if gpstime:
                localtime = dateutil.parser.parse(gpstime).astimezone(tzlocal())
                self.rowtext += [ScrollText("Time %s"  % localtime.strftime('%H:%M:%S'), self.cols)]
                self.rowtext += [ScrollText("Date %s"  % localtime.date(), self.cols)]
        else:
            self.rowtext = [
                ScrollText("No GPS fix", self.cols),
                ]
        self.rowidx = 0
