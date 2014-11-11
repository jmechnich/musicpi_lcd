import time, os, re, subprocess, sys

from musicpi_lcd.lcd import LCD
from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

class NetworkPrinter(Printer):
    PAGE_WIFI, PAGE_LOAD, PAGE_CTRL = range(3)
    
    def __init__(self, **kwargs):
        # configurable variables
        self.device    = 'wlan0'
        self.drivedir  = '/media/usb0'
        self.updatetimeout = 15
        self.gpsuser   = 'gps'
        super(NetworkPrinter,self).__init__(**kwargs)
        
        # internal variables
        self.ipre    = re.compile(r'inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        self.essidre = re.compile(r'ESSID:"([^\"]*)"')

    def init_layout(self):
        super(NetworkPrinter,self).init_layout()

        page = Page(self.lcd,idx=self.PAGE_WIFI)
        self.iptext    = page.add_scroll_line(header='IP')
        self.essidtext = page.add_scroll_line(header='ESSID')
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE_LOAD)
        self.timetext  = page.add_line()
        self.loadtext  = page.add_line()
        self.pages.append(page)
        
        page = Page(self.lcd,idx=self.PAGE_CTRL)
        page.add(CycleText(
                [ chr(LCD.SYM_RIGHT) + 'Restart wifi',
                  chr(LCD.SYM_UP)    + 'Sync USB drive', ],
                width=self.cols))
        page.add(CycleText(
                [ chr(LCD.SYM_LEFT)  + 'Reboot',
                  chr(LCD.SYM_DOWN)  + 'Restart logging', ],
                width=self.cols))
        self.pages.append(page)
        
        self.active = self.PAGE_WIFI
        
    def init(self):
        self.updatecounter = 0
        self.update()
        self.set_background()
        self.render(True)
        
    def render(self,force=False):
        self.updatecounter = (self.updatecounter+1)%self.updatetimeout
        if self.updatecounter == 0:
            self.update_changed(['load', 'date'])

        super(NetworkPrinter,self).render(force)

    def update_changed(self, changed_list=[], update_all=False):
        if update_all:
            changed = ['net', 'date', 'load']
        else:
            changed = changed_list

        for i in changed:
            if self.debug: print type(self).__name__, 'updating', changed
            if i == 'net':
                ifconfig_out = subprocess.check_output(["ifconfig",self.device])
                iwconfig_out = subprocess.check_output(["iwconfig",self.device])
                
                ipmatch = re.search( self.ipre, ifconfig_out)
                ip = "None"
                if ipmatch:
                    ip = ipmatch.groups()[0]
                self.iptext.setText(ip)
                    
                essidmatch = re.search( self.essidre, iwconfig_out)
                essid = ""
                if essidmatch:
                    essid = essidmatch.groups()[0]
                self.essidtext.setText(essid)
            elif i == 'date':
                cur =  time.strftime("%D %H:%M")
                if cur != self.timetext.text:
                    self.timetext.setText(cur)
            elif i == 'load':
                output = ' '.join( subprocess.check_output( "uptime").split()[-3:])
                if output != self.loadtext.text:
                    self.loadtext.setText(output)
        
    def update(self):
        if self.debug: print type(self).__name__ + " update"
        self.update_changed(update_all=True)
            
    def restart_wifi(self):
        self.show_splash("Restarting " + self.device,timeout=0)
        output = subprocess.check_output(['ifdown',self.device])
        if self.debug: print output
        subprocess.check_output(['ifup'  ,self.device])
        if self.debug: print output
        self.update_changed(['net'])
        self.active = self.PAGE_WIFI
        
    def reboot(self):
        self.show_splash("Rebooting")
        output = subprocess.check_output('shutdown -r now'.split())
        if self.debug: print output
        self.lcd.off()
    
    def sync_drive(self):
        self.show_splash("Syncing drive\n%s" % self.drivedir, timeout=0)
        stdout = None
        stderr = None
        if self.debug:
            stdout = sys.stdout
            stderr = sys.stderr
        cmd_mount_rw = "mount -o remount,rw,exec %s" % self.drivedir
        cmd_sync     = os.path.join(self.drivedir, "mediasync_music.sh")
        cmd_mount_ro = "mount -o remount,ro,noexec %s" % self.drivedir

        task_mount_rw = subprocess.Popen(cmd_mount_rw.split(),stdout=stdout,stderr=stderr)
        task_mount_rw.wait()
        
        print cmd_sync.split(), self.drivedir
        task_sync = subprocess.Popen(cmd_sync.split(),cwd=self.drivedir,stdout=stdout,stderr=stderr)
        task_sync.wait()

        task_mount_ro = subprocess.Popen(cmd_mount_ro.split(),stdout=stdout,stderr=stderr)
        task_mount_ro.wait()
        
    def restart_logging(self):
        self.show_splash("Restart logging")
        stdout = None
        stderr = None
        if self.debug:
            stdout = sys.stdout
            stderr = sys.stderr

        cmd_kill = 'sudo -u %s killall gpxlogger' % self.gpsuser
        cmd_exec = 'sudo /usr/local/sbin/start_gpxlogger.sh'
         
        task_kill = subprocess.Popen(cmd_kill.split(),stdout=stdout,stderr=stderr)
        task_kill.wait()
        task_exec = subprocess.Popen(cmd_exec.split(),stdout=stdout,stderr=stderr)
        task_exec.wait()

    def button_pressed_long(self,btn):
        if self.active == self.PAGE_CTRL:
            if btn == LCD.RIGHT:
                self.restart_wifi()
            elif btn == LCD.LEFT:
                self.reboot()
            elif btn == LCD.UP:
                self.sync_drive()
            elif btn == LCD.DOWN:
                self.restart_logging()
