import time, os, re, subprocess, sys, psutil

from lcd import LCD
from printer import Printer
from text    import *

class SystemPrinter(Printer):
    
    def __init__(self, **kwargs):
        self.PAGES = [ 'WIFI', 'LOAD', 'STAT', 'CTRL' ]
        # configurable variables
        self.device    = 'wlan0'
        self.drivedir  = '/media/usb0'
        self.updatetimeout = 15
        self.gpsuser   = 'gps'
        super(SystemPrinter,self).__init__(**kwargs)
        self.TASKS = [ 'net', 'load', 'date', 'daemon' ]
        self.DEPS  = {
            self.PAGE.WIFI: ['net'],
            self.PAGE.LOAD: ['load','date'],
            self.PAGE.STAT: ['daemon'],
            self.PAGE.CTRL: [],
            }
        # internal variables
        self.ipre    = re.compile(r'inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        self.essidre = re.compile(r'ESSID:"([^\"]*)"')

    def init_layout(self):
        super(SystemPrinter,self).init_layout()

        page = Page(self.lcd,idx=self.PAGE.WIFI)
        self.iptext    = page.add_scroll_line(header='IP')
        self.essidtext = page.add_scroll_line(header='ESSID')
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.LOAD)
        self.timetext  = page.add_line()
        self.loadtext  = page.add_line()
        self.pages.append(page)
        
        page = Page(self.lcd,idx=self.PAGE.STAT)
        page.add_line(Text('Daemon XNJ MSG'))
        page.add(Text('Status '))
        self.logger_status = page.add(Text(width=4))
        self.daemon_status = page.add(Text(width=5))
        self.pages.append(page)

        page = Page(self.lcd,idx=self.PAGE.CTRL)
        page.add(Text(chr(LCD.SYM_LEFT)))
        page.add(ScrollText('Reboot',     width=7))
        page.add(Text(chr(LCD.SYM_RIGHT)))
        page.add(ScrollText('ResetWifi', width=7))
        page.add(Text(chr(LCD.SYM_UP)))
        page.add(ScrollText('SyncUSB',   width=7))
        page.add(Text(chr(LCD.SYM_DOWN)))
        page.add(ScrollText('ResetLog', width=7))
        self.pages.append(page)

        self.set_active(self.PAGE.WIFI)
        
    def init(self):
        self.updatecounter = 0
        self.set_background()
        self.set_active(self.PAGE.WIFI)
        self.render(True)
        
    def render(self,force=False):
        self.updatecounter = (self.updatecounter+1)%self.updatetimeout
        if force:
            self.updatecounter = 0
        if self.updatecounter == 0:
            self.update(self.DEPS[self.active])
            
        super(SystemPrinter,self).render(force)

    def update(self, changed=[]):
        if not len(changed):
            return
        
        self.logger.debug('%s updating %s' % (type(self).__name__, str(changed)))
        for i in changed:
            if i == 'net':
                ifconfig_out = subprocess.check_output(["ifconfig",self.device])
                iwconfig_out = subprocess.check_output(["iwconfig",self.device])
                
                ipmatch = re.search( self.ipre, ifconfig_out)
                ip = "None"
                if ipmatch:
                    ip = ipmatch.groups()[0]
                self.iptext.setText(ip.rjust(self.iptext.width))
                    
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
            elif i == 'daemon':
                gpxlogger, gpspipe, start_wlan = 0, 0, 0
                stat_mpd, stat_shairport, stat_gmediarender = 0, 0, 0 
                for p in psutil.get_process_list():
                    try:
                        if p.username == 'gps':
                            if p.name == 'gpxlogger':
                                gpxlogger = 1
                                continue
                            elif p.name == 'gpspipe':
                                gpspipe = 1
                                continue
                            elif p.name == 'python' and p.cmdline[1].find('scan_wlan') != -1:
                                start_wlan = 1
                        elif p.username == 'mpd':
                            if p.name.endswith('mpd'):
                                stat_mpd = 1
                        else:
                            if p.name.endswith('shairport'):
                                stat_shairport = 1
                            elif p.name.endswith('gmediarender'):
                                stat_gmediarender = 1
                    except:
                        continue
                self.logger_status.setText("".join( ['*' if d else ' ' for d in [gpxlogger, gpspipe, start_wlan]] ))
                self.daemon_status.setText("".join( ['*' if d else ' ' for d in [stat_mpd, stat_shairport, stat_gmediarender]] ))
                
    def restart_wifi(self):
        self.show_splash("Restarting " + self.device,timeout=0)
        self.logger.info("Restarting "+ self.device)
        try:
            output = subprocess.check_output(['ifdown',self.device],stderr=subprocess.STDOUT)
            self.log_output(output)
            output = subprocess.check_output(['ifup'  ,self.device],stderr=subprocess.STDOUT)
            self.log_output(output)
            self.show_splash("Success")
        except:
            self.show_splash("Failed")
        self.update(['net'])
        self.set_active(self.PAGE.WIFI)
        self.logger.info("Restarted " + self.device)
        
    def reboot(self):
        self.show_splash("Rebooting")
        self.logger.info("Rebooting")
        try:
            output = subprocess.check_output('shutdown -r now'.split(),stderr=subprocess.STDOUT)
            self.log_output(output)
            self.exit = True
        except:
            self.show_splash("Failed")
    
    def sync_drive(self):
        self.show_splash("Syncing drive\n%s" % self.drivedir, timeout=0)
        self.logger.info("Syncing drive %s" % self.drivedir)

        cmd_mount_rw = "mount -o remount,rw,exec %s" % self.drivedir
        cmd_sync     = os.path.join(self.drivedir, "mediasync_music.sh")
        cmd_mount_ro = "mount -o remount,ro,noexec %s" % self.drivedir
        
        try:
            output = subprocess.check_output(cmd_mount_rw.split(),stderr=subprocess.STDOUT)
            self.log_output(output)
            output = subprocess.check_output(cmd_sync.split(),cwd=self.drivedir,stderr=subprocess.STDOUT)
            self.log_output(output)
            output = subprocess.check_output(cmd_mount_ro.split(),stderr=subprocess.STDOUT)
            self.log_output(output)
        except:
            self.show_splash("Failed")
        self.logger.info("Syncing finished")
    
    def restart_logging(self):
        self.show_splash("Restart logging")
        self.logger.info("Restarting GPS logging")

        cmd_kill = 'sudo -u %s killall gpxlogger' % self.gpsuser
        cmd_exec = 'sudo /usr/local/sbin/start_gpxlogger.sh'
        
        try:
            output = subprocess.check_output(cmd_kill.split(),stderr=subprocess.STDOUT)
            self.log_output(output)
            output = subprocess.check_output(cmd_exec.split(),stderr=subprocess.STDOUT)
            self.log_output(output)
        except:
            self.show_splash("Failed")
        self.logger.info("GPS logging restarted")

    def button_pressed_long(self,btn):
        if self.active == self.PAGE.CTRL:
            if btn == LCD.RIGHT:
                self.restart_wifi()
            elif btn == LCD.LEFT:
                self.reboot()
            elif btn == LCD.UP:
                self.sync_drive()
            elif btn == LCD.DOWN:
                self.restart_logging()
