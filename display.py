#!/usr/bin/env python

from musicpi_lcd.lcd         import LCD
from musicpi_lcd.printer_net import NetworkPrinter
from musicpi_lcd.printer_mpd import MPDPrinter
from musicpi_lcd.printer_gps import GPSPrinter
from musicpi_lcd.util        import colors, buttons
from musicpi_lcd.loop        import Loop

def main():
    lcd = LCD()
    cols = 16
    rows = 2
    ticklength = 0.5
    
    args = {
        'lcd':  lcd,
        'cols': cols,
        'rows':  rows,
        'ticklength': ticklength,
        }
    printers  = [
        MPDPrinter(**args),
        GPSPrinter(**args),
        NetworkPrinter(**args),
        ]
    loop = Loop(printers=printers, **args)
    try:
        while True:
            loop.iterate()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
