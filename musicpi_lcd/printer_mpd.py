import subprocess

import Adafruit_CharLCD  as LCD

from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import ScrollText
from musicpi_lcd.util    import colors

import mpd

class MPDPrinter(Printer):
    def __init__(self,**kwargs):
        super(MPDPrinter,self).__init__(**kwargs)
        self.mpd = mpd.MPDClient()
        
    def init(self):
        self.mpd.connect('localhost', 6600)
        status = self.mpd.status()
        print status
        current = self.mpd.currentsong()
        print current
        self.mpd.disconnect()
        
        self.rowtext = []

        text = ""
        
        text += (status['volume']+"%  ")
        text += status['state']

        flags  = ""
        flags += "C" if int(status['consume']) else " "
        flags += "R" if int(status['repeat']) else " "
        flags += "S" if int(status['random']) else " "
        flags += "1" if int(status['single']) else " "
        text += flags.rjust(self.cols-len(text))
        self.rowtext += [ScrollText(text,self.cols)]
        
        
        self.lcd.set_color(*colors['green'])
        self.rowidx = 0

    def call_mpd(self,cmd):
        ret = self.mpd.__getattr__(cmd)()
        self.mpd.disconnect()
        return ret
    
    def button_pressed(self,btn):
        if btn == LCD.RIGHT:
            self.call_mpd('next')
        elif btn == LCD.DOWN:
            self.call_mpd('stop')
        elif btn == LCD.UP:
            self.call_mpd('play')
        elif btn == LCD.LEFT:
            self.call_mpd('previous')
