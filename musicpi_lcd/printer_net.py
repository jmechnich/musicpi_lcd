import re, subprocess

from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

import Adafruit_CharLCD as LCD

class NetworkPrinter(Printer):
    def __init__(self, **kwargs):
        self.device = 'wlan0'
        super(NetworkPrinter,self).__init__(**kwargs)
        
    def init(self):
        self.update()
        self.set_background()
        self.active = 0
        self.render(True)
        
    def update(self):
        ipre    = re.compile(r'inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        essidre = re.compile(r'ESSID:"([^\"]*)"')
        ifconfig_out = subprocess.check_output(["ifconfig",self.device])
        ipmatch = re.search( ipre, ifconfig_out)
        iwconfig_out = subprocess.check_output(["iwconfig",self.device])
        essidmatch = re.search( essidre, iwconfig_out)
        ip = "None"
        if ipmatch:
            ip = ipmatch.groups()[0]
        essid = ""
        if essidmatch:
            essid = essidmatch.groups()[0]
            
        page = Page()
        page.add_scroll_line(ip,header="IP")
        page.add_scroll_line(essid,header="ESSID")
        
        self.pages = [ page ]

    def reset_wifi(self):
        print subprocess.check_output(['ifdown','wlan0'])
        print subprocess.check_output(['ifup','wlan0'])
        
    def button_pressed_long(self,btn):
        if btn == LCD.RIGHT:
            self.reset_wifi()
            

