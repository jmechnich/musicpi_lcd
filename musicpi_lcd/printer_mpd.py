import subprocess

from musicpi_lcd.lcd     import LCD
from musicpi_lcd.printer import Printer
from musicpi_lcd.text    import *

from mpd import MPDClient
from threading import Thread, Lock, Event

class MPDThread(Thread):
    def __init__(self,mpdhost,mpdport):
        self.mpd = MPDClient()
        self.host = mpdhost
        self.port = mpdport
        super(MPDThread,self).__init__()
        self._changed = []
        self._lock = Lock()
        self._stop = Event()
        
    def run(self):
        self._stop.clear()
        self.append_changed(['player', 'options', 'mixer', 'update'])
        self.mpd.connect(self.host,self.port)
        while not self._stop.is_set():
            self.subsys = self.mpd.idle()
            self.append_changed(self.subsys)
        self.mpd.disconnect()
        
    def stop(self):
        self._stop.set()
        self.mpd.noidle()

    def append_changed(self,changed):
        with self._lock:
            self._changed += changed

    def release_changed(self):
        with self._lock:
            old = self._changed
            self._changed = []
        return old
        
def strtime(seconds):
    seconds = float(seconds)
    minutes = seconds/60
    hours   = minutes/60
    ret = ":%02d" %(round(seconds)%60)
    if hours >=1:
        ret = ("%d:%02d" % (int(hours),int(minutes)%60)) + ret
    else:
        ret = ("%d" % (int(minutes)%60)) + ret
    return ret

def strswitch(state):
    """ """
    return 'on' if state else 'off'

class MPDPrinter(Printer):
    PAGE_PLAYER, PAGE_OPTIONS = range(2)
    
    def __init__(self,**kwargs):
        # configurable variables
        self.mpdhost = 'localhost'
        self.mpdport = 6600

        super(MPDPrinter,self).__init__(**kwargs)
        
        # internal variables
        self._mpd = MPDClient()
        self._thread = None

    def init_layout(self):
        super(MPDPrinter,self).init_layout()
        
        page = Page(self.lcd,idx=self.PAGE_PLAYER)
        self.statetext = page.add(Text(width=1))
        self.songtext  = page.add(ScrollText(width=page.cols-1))
        page.newline()
        
        self.plstext   = page.add(ScrollText(width=5))
        self.timetext  = page.add(ScrollText(width=page.cols-self.plstext.width))
        self.pages.append(page)
        
        page = Page(self.lcd,idx=self.PAGE_OPTIONS)
        self.opttext    = page.add(CycleText(width=11))
        self.volumetext = page.add(Text(width=page.cols-self.opttext.width))
        page.newline()
        
        self.updatetext = CycleText(
            [ chr(LCD.SYM_UP)   + "Update " + chr(LCD.SYM_DOWN) + "Up RAM ",
              chr(LCD.SYM_LEFT) + "Vol-   " + chr(LCD.SYM_RIGHT)+ "Vol+   ",
              ],
            width=page.cols-1)
        page.add(self.updatetext)
        self.updatestatus = page.add(Text(width=1))
        self.pages.append(page)

        self.active = self.PAGE_PLAYER
        
    def __del__(self):
        self.stop()

    def stop(self):
        if not self._thread:
            return
        if not self._thread.is_alive():
            if self.debug: print type(self).__name__, ": Thread not running"
        if self.debug: print type(self).__name__, ": Stopping thread"
        self._thread.stop()
        self._thread.join()
        self._thread = None
        if self.debug: print type(self).__name__, ": Thread stopped"
        
    def init(self):
        if not self._thread:
            self._thread = MPDThread(self.mpdhost,self.mpdport)
            self._thread.start()
        self.lcd.set_color(*self.color)
        self.active = 0
        self.render(True)
    
    def render(self,force=False):
        self.update_changed(self._thread.release_changed())
        super(MPDPrinter,self).render(force)
    
    def update_changed(self,changed_list=[], update_all=False):
        if update_all:
            changed = ['player', 'options', 'mixer', 'update']
        else:
            changed = changed_list[:]

        self._mpd.connect(self.mpdhost, self.mpdport)
        status = self._mpd.status()
        current = self._mpd.currentsong()
        self._mpd.disconnect()
        
        if self.debug: print type(self).__name__, 'updating', changed
        for i in changed:
            if i == 'player':
                songtext = "%s - %s" % (current.get('artist', '<Unknown Artist>'),
                                        current.get('title',  '<Unknown Title>'))
                self.songtext.setText(songtext)
                state = status['state']
                if state == 'play':
                    state = LCD.SYM_PLAY
                elif state == 'pause':
                    state = LCD.SYM_PAUSE
                else:
                    state = LCD.SYM_STOP
                self.statetext.setText(chr(state))
                plstext = ("%d/%d" % (int(status.get('song', '-1'))+1,int(status.get('playlistlength', '-1'))))
                self.plstext.setText( plstext.ljust(self.plstext.width))
            elif i == 'options':
                self.opttext.setList(
                    [
                        'Repeat '.ljust(8) + strswitch(int(status['repeat'])).rjust(3),
                        'Consume'.ljust(8) + strswitch(int(status['consume'])).rjust(3),
                        'Random '.ljust(8) + strswitch(int(status['random'])).rjust(3),
                        'Single '.ljust(8) + strswitch(int(status['single'])).rjust(3),
                        ]
                    )
            elif i == 'mixer':
                volumetext = status['volume']+"%"
                self.volumetext.setText(volumetext.rjust(self.volumetext.width))
            elif i == 'update':
                self.updatestatus.setText( chr(LCD.SYM_CLOCK) if status.get('updating_db', False) else ' ')
            else:
                if self.debug: print type(self).__name__, "unhandled event", i
        timetext = '/'.join( [ strtime(i) for i in status.get('time', '0:0').split(':') ])
        self.timetext.setText( timetext.rjust(self.timetext.width))
        
    def update(self):
        if self.debug: print type(self).__name__ + " update"
        self.update_changed(update_all=True)
            
    def call_mpd(self,cmd, *args):
        self._mpd.connect(self.mpdhost, self.mpdport)
        ret = self._mpd.__getattr__(cmd)(*args)
        self._mpd.disconnect()
        return ret

    def toggle_play(self):
        self._mpd.connect(self.mpdhost, self.mpdport)
        status = self._mpd.status()
        if status['state'] == 'play':
            self._mpd.pause()
        else:
            self._mpd.play()
        self._mpd.disconnect()

    def button_pressed(self,btn,repeat):
        if self.active == self.PAGE_PLAYER:
            if btn == LCD.RIGHT:
                self.call_mpd('next')
            elif btn == LCD.LEFT:
                self.call_mpd('previous')
            elif btn == LCD.DOWN and not repeat:
                self.call_mpd('stop')
            elif btn == LCD.UP and not repeat:
                self.toggle_play()
        elif self.active == self.PAGE_OPTIONS:
            volumetext = self.volumetext.text[:-1]
            if len(volumetext):
                volume = int(volumetext)
                if btn == LCD.RIGHT:
                    volume = min(volume+5,100)
                    self.call_mpd('setvol', volume)
                    self.volumetext.setText("%d%%" % volume)
                elif btn == LCD.LEFT:
                    volume = max(volume-5,0)
                    self.call_mpd('setvol', volume)
                    self.volumetext.setText("%d%%" % volume)
            if btn == LCD.UP and not repeat:
                if self.updatestatus.text == ' ':
                    self.show_splash('Updating all')
                    self.call_mpd('update')
                else:
                    self.show_splash('Update in\nprogress')
            elif btn == LCD.DOWN and not repeat:
                if self.updatestatus.text == ' ':
                    self.show_splash('Updating ramdisk')
                    self.call_mpd('update', 'RAMDISK')
                else:
                    self.show_splash('Update in\nprogress')
        super(MPDPrinter,self).button_pressed(btn,repeat)
