
# Extension fo "neopixel" leds for manageing a LCD backlight
#
# Copyright (C) 2021  Olivier Bossi <olivier.bossi@protonmail.ch>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging

class PrinterNeoPixelBacklight:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        self.name = config.get_name().split()[1]

        self.red = config.getfloat('RED', 0., minval=0., maxval=1.)
        self.green = config.getfloat('GREEN', 0., minval=0., maxval=1.)
        self.blue = config.getfloat('BLUE', 0., minval=0., maxval=1.)
        
        self.dim_red = config.getfloat('dim_RED', 0., minval=0., maxval=1.)
        self.dim_green = config.getfloat('dim_GREEN', 0., minval=0., maxval=1.)
        self.dim_blue = config.getfloat('dim_BLUE', 0., minval=0., maxval=1.)
        
        self.timeout_dim = config.getfloat('timeout_dim', 0., minval=0., maxval=1E6)*60
        self.timeout_off = config.getfloat('timeout_off', 0., minval=0., maxval=1E6)*60
        
        neopixels = self.printer.lookup_objects('neopixel')
        for neopixel in neopixels:
            (mod,obj) = neopixel
            if(mod.split()[1] == self.name):
                self.neopixel = obj
                
        if(self.neopixel == None):
            raise config.error("No neopixel named ".format(name))

        gcode = self.printer.lookup_object('gcode')
        gcode.register_mux_command("LCD_WAKEUP", "LED", self.name, self.cmd_LCD_WAKEUP,
                                   desc=self.cmd_LCD_WAKEUP_help)
        
        eventtime = self.reactor.monotonic() 
        self.timer = self.reactor.register_timer(self._update_callback)

        self.printer.register_event_handler("klippy:connect", self._handle_wakeup)
        self.printer.register_event_handler("ui:wakeup", self._handle_wakeup)
 
    cmd_LCD_WAKEUP_help = "Force wakeup of neopixel LCD backlight"
    
    def cmd_LCD_WAKEUP(self, gcmd):
        self._handle_wakeup()
    
    def _handle_wakeup(self):
        logging.info("Received UI wakeup event")
        self.next = "ON"
        self.reactor.update_timer(self.timer,self.reactor.NOW)

        
    def _update_callback(self,eventtime):
        
        if self.next == "DIM":
            logging.info("Dimming neopixel " + self.name)
            self.neopixel.cmd_exec(self.dim_red,self.dim_green,self.dim_blue,0)
            if self.timeout_off>0:
                self.next = "OFF"
                return eventtime + self.timeout_off
            else:
                self.next = "WAIT"
                return self.reactor.NEVER
 
        if self.next=="OFF" :
            logging.info("Shutting down neopixel " + self.name)
            self.neopixel.cmd_exec(0,0,0,0)
            self.next="WAIT"
            return self.reactor.NEVER   
            
        if self.next=="ON":
            logging.info("Wakeing up neopixel " + self.name)
            self.neopixel.cmd_exec(self.red,self.green,self.blue,0)
            if self.timeout_dim>0:
                self.next = "DIM"
                return eventtime + self.timeout_dim
            elif self.timeout_off>0:
                self.next = "OFF"
                return eventtime + self.timeout_off
            else:
                self.next = "WAIT"
                return self.reactor.NEVER
                
        return self.reactor.NEVER

def load_config_prefix(config):
    return PrinterNeoPixelBacklight(config)
