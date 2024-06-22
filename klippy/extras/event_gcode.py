# Support for running gcode after internal klipper events
#
# Copyright (C) 2021  Olivier Bossi <olivier.bossi@protonmail.ch>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging

class EventGcode:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.name = config.get_name().split()[1]
        self.gcode = self.printer.lookup_object('gcode')
        gcode_macro = self.printer.load_object(config, 'gcode_macro')
        self.event_gcode = gcode_macro.load_template(config, 'gcode')

        self.enabled = config.getboolean('enabled',True)
        self.event = config.get('event','klippy:none')
        self.delay = config.getfloat('delay', 0., minval=0.)
        self.cooldown_delay = config.getfloat('cooldown_delay', 0., minval=0.)

        self.timer = self.reactor.register_timer(self._handle_timer_event)

        self.last_execution = self.reactor.NOW

        self.gcode.register_mux_command("EVENT_GCODE_ENABLE",
            "ID", self.name, self.cmd_EVENT_GCODE_ENABLE,
            desc=self.cmd_EVENT_GCODE_ENABLE_help)

        self.gcode.register_mux_command("EVENT_GCODE_DISABLE",
            "ID",self.name, self.cmd_EVENT_GCODE_DISABLE,
            desc=self.cmd_EVENT_GCODE_DISABLE_help)

        self.gcode.register_mux_command("EVENT_GCODE_TRIGGER",
            "ID", self.name, self.cmd_EVENT_GCODE_TRIGGER,
            desc=self.cmd_EVENT_GCODE_TRIGGER_help)

        self.gcode.register_mux_command("EVENT_GCODE_CANCEL",
           "ID", self.name, self.cmd_EVENT_GCODE_CANCEL,
            desc=self.cmd_EVENT_GCODE_CANCEL_help)

        self.printer.register_event_handler(self.event, self._handle_event)

    def _handle_event(self):
        if self.enabled:
            eventtime = self.reactor.monotonic()
            self.reactor.update_timer(self.timer,eventtime+self.delay)

    def _handle_timer_event(self, eventtime):
        if (eventtime-self.last_execution)>self.cooldown_delay:
            try:
                self.gcode.run_script(self.event_gcode.render())
            except Exception:
                logging.exception("Script running error")
            self.last_execution = eventtime
        return self.reactor.NEVER

    cmd_EVENT_GCODE_ENABLE_help = "Enable execution of an event_gcode"
    def cmd_EVENT_GCODE_ENABLE(self,gcmd):
        self.enabled = True

    cmd_EVENT_GCODE_DISABLE_help = "Disable execution of an event_gcode"
    def cmd_EVENT_GCODE_DISABLE(self,gcmd):
        self.reactor.update_timer(self.timer,self.reactor.NEVER)
        self.enabled = False

    cmd_EVENT_GCODE_TRIGGER_help = "Trigger execution of an event_gcode"
    def cmd_EVENT_GCODE_TRIGGER(self,gcmd):
        self._handle_event()

    cmd_EVENT_GCODE_CANCEL_help = "Cancel execution of an event_gcode"
    def cmd_EVENT_GCODE_CANCEL(self,gcmd):
        self.reactor.update_timer(self.timer,self.reactor.NEVER)

def load_config_prefix(config):
    return EventGcode(config)
