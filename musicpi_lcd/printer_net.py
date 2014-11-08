import re, subprocess

from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

class NetworkPrinter(Printer):
    def __init__(self, **kwargs):
        super(NetworkPrinter,self).__init__(**kwargs)
    
    def init(self):
        self.update()
        self.active = 0
        self.lcd.set_color(*self.color)
        self.render(True)
        
    def update(self):
        ipre    = re.compile(r'inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        essidre = re.compile(r'ESSID:"([^\"]*)"')
        ifconfig_out = subprocess.check_output(["ifconfig","wlan0"])
        ipmatch = re.search( ipre, ifconfig_out)
        iwconfig_out =  subprocess.check_output(["iwconfig","wlan0"])
        essidmatch = re.search( essidre, iwconfig_out)
        ip = "None"
        if ipmatch:
            ip = ipmatch.groups()[0]
        essid = ""
        if essidmatch:
            essid = essidmatch.groups()[0]
            
        page = Page()
        ipheader = "IP "
        page.add(Text(ipheader))
        width = self.cols-len(ipheader)
        page.add(ScrollText(ip,width=width))
        essidheader = "ESSID "
        page.add(Text(essidheader))
        width = self.cols-len(essidheader)
        page.add(ScrollText(essid,width=width))
        
        self.pages = [ page ]
