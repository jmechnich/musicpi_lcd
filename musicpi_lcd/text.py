class Text(object):
    def __init__(self, text="", width=-1):
        self.text  = text
        if width < 0:
            width = len(self.text)
        self.width = width
        self.changed = True
    def __str__(self):
        return self.text[:self.width].ljust(self.width)

    def setText(self,text):
        self.changed = (text != self.text)
        self.text = text
        
    def update(self):
        ret = self.changed
        if self.changed:
            self.changed = False
        return ret
    
class CycleText(Text):
    def __init__(self, textlist=[], width=-1,initial=0, delay=5):
        self.textlist = textlist
        self.counter  = initial
        self.delay    = delay
        self.delaycounter = 0
        if width < 0:
            width = len(max(self.textlist,key=len))
        
        if len(self.textlist) > initial and len(self.textlist[initial]):
            text = self.textlist[initial]
        else:
            text = ''
        super(CycleText,self).__init__(text,width)
 
    def setList(self,textlist):
        self.textlist = textlist
        if not self.counter < len(self.textlist):
            self.counter = 0
        self.delaycounter = 0
        
    def update(self):
        self.delaycounter = (self.delaycounter+1)%self.delay
        if self.delaycounter == 1:
            if len(self.textlist):
                self.counter = (self.counter+1)%len(self.textlist)
                self.text = self.textlist[self.counter].ljust(self.width)
            return True
        return False


class ScrollText(Text):
    def __init__(self,scrolltext="",width=-1,wait=5,inc=1):
        self.scrolltext = None
        if width < 0: width = len(scrolltext)
        self.wait = wait
        self.inc  = inc
        super(ScrollText,self).__init__(width=width)
        self.setText(scrolltext)
    
    def setText(self, text):
        if text == self.scrolltext:
            return
        self.scrolltext = text
        dx = max(0,len(self.scrolltext)-self.width)
        self.loop    = [0]*self.wait + [self.inc]*dx + [0]*self.wait + [-self.inc]*dx
        self.counter = 0
        self.looppos = 0
        
    def update(self):
        ret = False
        text = self.scrolltext[self.looppos:self.looppos+self.width].ljust(self.width)
        if self.text != text:
            self.text = text
            ret = True
        self.looppos += self.loop[self.counter]
        self.counter = (self.counter+1)%len(self.loop)
        return ret

class Page(object):
    def __init__(self, lcd, idx=-1):
        self.lcd = lcd
        self.idx  = idx
        self.cols = self.lcd._cols
        self.rows = self.lcd._lines
        
        self.items = []
        self.pos = 0
    
    def pos_col(self):
        return self.pos%self.cols

    def pos_row(self):
        return self.pos/self.cols
    
    def add(self, text):
        if self.pos >= self.cols*self.rows:
            print "Warning: position larger than page size"
            print self.pos_col(), self.pos_row(), text.__dict__
        self.items += [ (self.pos, text) ]
        #print "Adding new item at", self.pos_col(), self.pos_row(), text
        self.pos += text.width
        return text

    def newline(self):
        col = self.pos_col()
        if col == 0:
            return
        self.pos = self.pos + self.cols-col
    
    def render(self, force=False):
        was_updated = False
        for pos, text in self.items:
            if (text.update() or force):
                self.pos = pos
                #print "Moving cursor to", self.pos_col(),self.pos_row()
                self.lcd.set_cursor(self.pos_col(),self.pos_row())
                #print "Rendering %s '%s' at %d, %d" % (type(text).__name__, str(text), self.pos_col(), self.pos_row())
                self.lcd.message( str(text))
                was_updated = True
        return was_updated

    def add_line(self,text=None,header=None):
        width = self.cols
        if not text:
            text = Text(width=width)
        if header:
            headertext = Text(header+" ") 
            self.add(headertext)
            width -= headertext.width
        text.width = width
        self.add(text)
        return text

    def add_scroll_line(self,rawtext='',header=None):
        return self.add_line(ScrollText(rawtext), header)
