import re, subprocess

from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import ScrollText
from musicpi_lcd.util    import colors

class NetworkPrinter(Printer):
    def __init__(self, **kwargs):
        super(NetworkPrinter,self).__init__(**kwargs)
    
    def init(self):
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
            
        ipheader = "IP"
        essidheader = "ESSID"
        
        self.lcd.set_cursor(0,0)
        self.lcd.message( ipheader.ljust(self.cols))
        self.lcd.set_cursor(0,1)
        self.lcd.message( essidheader.ljust(self.cols))
    
        ipstart = len(ipheader)+1
        essidstart = len(essidheader)+1
        ipmaxw    = self.cols - ipstart
        essidmaxw = self.cols - essidstart
    
        self.rowtext = [
            ScrollText(ip,ipmaxw),
            ScrollText(essid,essidmaxw),
            ]
        self.lcd.set_color(*colors['red'])
        self.rowidx = 0
