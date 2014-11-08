import subprocess

import Adafruit_CharLCD  as LCD

from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

from mpd import MPDClient
from threading import Thread, Lock

class MPDThread(Thread):
    def __init__(self,parent):
        self.mpd = MPDClient()
        self.host = parent.host
        self.port = parent.port
        self.parent = parent
        super(MPDThread,self).__init__()
        self.setDaemon(True)

    def run(self):
        self.mpd.connect(self.host,self.port)
        while True:
            self.subsys = self.mpd.idle()
            self.parent.append_changed(self.subsys)
        print "Disconnecting"
        self.mpd.disconnect()

def strtime(seconds):
    seconds = float(seconds)
    minutes = seconds/60
    hours   = minutes/60
    ret = ":%02d" %(round(seconds)%60)
    if hours >=1:
        ret = ("%d:%02d" % (round(hours),round(minutes)%60)) + ret
    else:
        ret = ("%d" % (round(minutes)%60)) + ret
    return ret

def strswitch(state):
    return 'on' if state else 'off'

class MPDPrinter(Printer):
    def __init__(self,**kwargs):
        super(MPDPrinter,self).__init__(**kwargs)
        
        self.mpd = MPDClient()
        self.host = 'localhost'
        self.port = 6600
        self.init_page()
        self.update_changed(update_all=True)
        self.lock = Lock()
        self.mpdthread = MPDThread(self)
        self.mpdthread.start()
        self.changed = []

    def init_page(self):
        self.pages = []

        page = Page()
        self.songtext = ScrollText(width=page.cols)
        page.add( self.songtext)
        page.newline()
        
        self.plstext  = Text(width=6)
        self.timetext = Text(width=10)
        page.add( self.plstext)
        page.add( self.timetext)
        self.pages.append(page)
        
        page = Page()
        self.opttext    = CycleText(width=11)
        self.volumetext = Text(width=5)
        page.add( self.opttext)
        page.add( self.volumetext)
        page.newline()
        
        placeholder     = Text('ABCDEFGHIJKLMNOP')
        page.add( placeholder)
        self.pages.append(page)
        
    def append_changed(self,changed):
        self.lock.acquire()
        self.changed += changed
        self.lock.release()

    def retrieve_changed(self):
        self.lock.acquire()
        old = self.changed
        self.changed = []
        self.lock.release()
        return old
        
    def init(self):
        self.lcd.set_color(*self.color)
        self.active = 0
        self.render(True)
    
    def render(self,force=False):
        changed = self.retrieve_changed()
        if len(changed):
            self.update_changed(changed)
            force = True
        else:
            self.update_changed()
        super(MPDPrinter,self).render(force)
    
    def update_changed(self,changed=[], update_all=False):
        self.mpd.connect(self.host, self.port)
        status = self.mpd.status()
        current = self.mpd.currentsong()
        self.mpd.disconnect()
        
        if update_all or 'player' in changed:
            songtext = "%s - %s" % (current.get('artist', '<Unknown Artist>'),
                                    current.get('title',  '<Unknown Title>'))
            self.songtext.setText(songtext)
            plstext = ("%d/%d" % (int(status.get('song', '-1'))+1,int(status.get('playlistlength', '-1'))))
            self.plstext.setText( plstext.ljust(self.plstext.width))
        if update_all or 'options' in changed:
            self.opttext.setList(
                [
                    'Repeat '.ljust(8) + strswitch(int(status['repeat'])).rjust(3),
                    'Consume'.ljust(8) + strswitch(int(status['consume'])).rjust(3),
                    'Random '.ljust(8) + strswitch(int(status['random'])).rjust(3),
                    'Single '.ljust(8) + strswitch(int(status['single'])).rjust(3),
                    ]
                )
        if update_all or 'mixer' in changed:
            volumetext = status['volume']+"%"
            self.volumetext.setText(volumetext.rjust(self.volumetext.width))
        timetext = '/'.join( [ strtime(i) for i in status.get('time', '0:0').split(':') ])
        self.timetext.setText( timetext.rjust(10))

    def update(self):
        self.update_changed(update_all=True)
            
    def call_mpd(self,cmd):
        self.mpd.connect(self.host, self.port)
        ret = self.mpd.__getattr__(cmd)()
        self.mpd.disconnect()
        return ret

    def toggle_play(self):
        self.mpd.connect(self.host, self.port)
        status = self.mpd.status()
        if status['state'] == 'play':
            self.mpd.pause()
        else:
            self.mpd.play()
        self.mpd.disconnect()
    
    def button_clicked(self,btn):
        if btn == LCD.RIGHT:
            self.call_mpd('next')
        elif btn == LCD.DOWN:
            self.call_mpd('stop')
        elif btn == LCD.UP:
            self.toggle_play()
        elif btn == LCD.LEFT:
            self.call_mpd('previous')
