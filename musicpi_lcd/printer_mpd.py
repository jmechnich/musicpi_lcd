import subprocess

from lcd     import LCD
from printer import Printer
from text    import *
from thread  import BaseThread as Thread

from mpd import MPDClient, MPDError

class MPDThread(Thread):
    def __init__(self,mpdhost,mpdport,logger):
        super(MPDThread,self).__init__(logger)
        self.mpd = MPDClient()
        self.host = mpdhost
        self.port = mpdport
        
    def run(self):
        try:
            self.mpd.connect(self.host,self.port)
            while self.iterate():
                self.subsys = self.mpd.idle()
                self.set_data(self.subsys)
            self.mpd.disconnect()
        except MPDError, e:
            self.logger.debug('%s' % str(e))
        
    def stop_iterate(self):
        self.mpd.noidle()

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
    def __init__(self,**kwargs):
        self.PAGES = ['PLAYER', 'OPTIONS']
        # configurable variables
        self.mpdhost = 'localhost'
        self.mpdport = 6600

        super(MPDPrinter,self).__init__(**kwargs)
        self.TASKS = ['player', 'playlist', 'options', 'mixer', 'update']
        self.DEPS  = {
            self.PAGE.PLAYER:  ['player', 'playlist'],
            self.PAGE.OPTIONS: ['options', 'mixer', 'update'],
            }
        # internal variables
        self._mpd = MPDClient()
        self._thread = None

    def init_layout(self):
        super(MPDPrinter,self).init_layout()
        
        page = Page(self.lcd,idx=self.PAGE.PLAYER)
        self.statetext = page.add(Text(width=1))
        self.songtext  = page.add(ScrollText(width=page.cols-1))
        page.newline()
        
        self.plstext   = page.add(ScrollText(width=5))
        self.timetext  = page.add(ScrollText(width=page.cols-self.plstext.width))
        self.pages.append(page)
        
        page = Page(self.lcd,idx=self.PAGE.OPTIONS)
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

        self.set_active(self.PAGE.PLAYER)
        
    def __del__(self):
        self.stop()

    def stop(self):
        if not self._thread:
            return
        self._thread.stop()
        self._thread = None
        
    def init(self):
        if not self._thread:
            self._thread = MPDThread(self.mpdhost,self.mpdport,self.logger)
            self._thread.start()
        self.lcd.set_color(*self.color)
        self.set_active(self.PAGE.PLAYER)
        self.render(True)
    
    def render(self,force=False):
        changed = self._thread.pop_data()
        if not changed:
            changed = []
        deps = self.DEPS[self.active]
        changed = [ i for i in changed if i in deps ] 
        if force:
            changed += deps
                    
        self.update(list(set(changed)))
        super(MPDPrinter,self).render(force)
    
    def update(self,changed=[]):
        self._mpd.connect(self.mpdhost, self.mpdport)
        status = self._mpd.status()
        if len(changed):
            current = self._mpd.currentsong()
        self._mpd.disconnect()
        
        timetext = '/'.join( [ strtime(i) for i in status.get('time', '0:0').split(':') ])
        self.timetext.setText( timetext.rjust(self.timetext.width))

        if not len(changed):
            return
        
        if 'player' in changed and not 'playlist' in changed:
            changed.append('playlist')
        
        self.logger.debug( '%s updating %s' % (type(self).__name__,str(changed)))
        for i in changed:
            if i == 'player':
                #print current
                artist = current.get('artist',None)
                album  = current.get('album' ,None)
                title  = current.get('title' ,None)
                genre  = current.get('genre' ,None)
                items = []
                if artist:
                    items.append(artist)
                if album and genre and genre in ['Books & Spoken', 'Drama', 'Podcast']:
                    items.append(album)
                if title:
                    items.append(title)
                songtext = " - ".join(items)
                self.songtext.setText(songtext)
                state = status['state']
                if state == 'play':
                    state = LCD.SYM_PLAY
                elif state == 'pause':
                    state = LCD.SYM_PAUSE
                else:
                    state = LCD.SYM_STOP
                self.statetext.setText(chr(state))
            elif i == 'playlist':
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
            elif i == 'sticker':
                pass
            else:
                self.logger.debug( "%s unhandled event %s" %( type(self).__name__, i))
        
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

    def button_clicked(self,btn):
        if self.active == self.PAGE.PLAYER:
            if btn == LCD.RIGHT:
                self.call_mpd('next')
            elif btn == LCD.LEFT:
                self.call_mpd('previous')
        super(MPDPrinter,self).button_clicked(btn)
        
    def button_pressed(self,btn,repeat):
        if self.active == self.PAGE.PLAYER:
            if (btn == LCD.LEFT or btn == LCD.RIGHT) and repeat:
                status = self.call_mpd('status')
                secs   = int(float(status['elapsed'])+0.5)
                songid = status['songid']
                if btn == LCD.RIGHT:
                    secs += 10
                    self.call_mpd('seek', songid, str(secs))
                elif btn == LCD.LEFT:
                    secs -= 10
                    self.call_mpd('seek', songid, str(secs))
            elif btn == LCD.DOWN and not repeat:
                self.call_mpd('stop')
            elif btn == LCD.UP and not repeat:
                self.toggle_play()
        elif self.active == self.PAGE.OPTIONS:
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
