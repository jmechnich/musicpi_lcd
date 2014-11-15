import logging

from musicpi_lcd.lcd  import LCD, buttons, colors
from musicpi_lcd.text import *

class Printer(object):
    def __init__(self,**kwargs):
        if not 'PAGES' in self.__dict__.keys():
            raise RuntimeError('PAGES not defined for %s' % type(self).__name__)
        self.PAGE  = type('PAGE', (object,), dict(
            [('N', len(self.PAGES))] + [(p,i) for i, p in enumerate(self.PAGES)]
            ))
    
        # configurable variables
        self.color = colors['white']
        self.splashticks = 1

        self.__dict__.update(kwargs)
        
        self.exit = False
        self.init_layout()

    def init_layout(self):
        self.pages = []
        self.active = -1
        self.btncounter = dict(zip(buttons,[0]*len(buttons)))
        self.longpress = 3
        self.splash = None
        self.splashcounter = 0

    def set_active(self, active):
        lastpage = len(self.pages)-1
        if active < 0:
            active = lastpage
        elif active > lastpage:
            active = 0
        self.logger.debug('%s set_active %s (previous: %s)' % (type(self).__name__,self.PAGES[active],self.PAGES[self.active] if self.active >= 0 else 'None'))
        self.active = active

    # main loop function
    def iterate(self):
        if self.exit:
           return False 
        self.render()
        return True
            
    # display functions
    def render(self,force=False):
        if self.splashcounter > 0 and not force:
            self.splashcounter -= 1
            return
        if self.splash:
            self.logger.debug( '%s hiding splash' % type(self).__name__)
            self.splashcounter = 0
            self.splash = None
            force = True
        if (self.active < 0) or (self.active >= len(self.pages)):
            return
        self.render_page( self.pages[self.active], force=force)

    def render_page(self, page, force=False):
        was_updated = page.render(force=force)
        #if was_updated:
        #    self.logger.debug('%s render_page force=%s' % (type(self).__name__, str(force)))

    # default button handlers
    def button_released(self,btn):
        pass
    
    def button_pressed(self,btn,repeat):
        pass
          
    def button_pressed_long(self,btn):
        pass
            
    def button_clicked(self,btn):
        if btn == LCD.SELECT:
            self.next_page()
    
    # default actions
    def show_splash(self,text,timeout=-1):
        self.splash = Page(self.lcd)
        words = text.split('\n')
        firstline  =  text.center(self.cols)
        secondline = ''
        if len(words) > 1:
            firstline  = ''.join(words[:len(words)/2]).center(self.cols)
            secondline = ''.join(words[len(words)/2:]).center(self.cols)
        self.splash.add(ScrollText(firstline,  width=self.cols))
        self.splash.add(ScrollText(secondline, width=self.cols))
        self.splashcounter = self.splashticks if timeout < 0 else timeout
        self.render_page(self.splash, force=True)
    
    def stop(self):
        pass
    
    def set_background(self):
        self.lcd.set_color(*self.color)
    
    def prev_page(self):
        self.set_active(self.active-1)
        self.render(force=True)

    def next_page(self):
        self.set_active(self.active+1)
        self.render(force=True)

    def log_output(self,output, lvl=logging.DEBUG):
        if self.logger.getEffectiveLevel() > lvl:
            return
        for line in output.split('\n'):
            if len(line.strip()) == 0:
                continue
            self.logger.log( lvl, line)
