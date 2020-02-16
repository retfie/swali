import asyncio
import struct
from .vscp.vscp_tcp import vscp_tcp
from .vscp.vscp_event import event
from .vscp.const import (CLASS_CONTROL, EVENT_CONTROL_TURN_ON, EVENT_CONTROL_TURN_OFF)

class light:
    def __init__(self, nick, channel, updater):
        self.nickname = nick
        self.channel = channel
        self.updater = updater
        self.callback = list()

    def from_raw(self, raw_input):
        self.state = (raw_input[2] != 0x00)
        self.enabled = (raw_input[3] != 0x00)
        self.zone = int(raw_input[4])
        self.subzone = int(raw_input[5])
        self.name = raw_input[16:33].decode().rstrip('/x0')

    async def update(self, state):
        self.state = state
        for c in self.callback:
            await c(self, self.state)

    async def set(self, state):
        if state:
            type = EVENT_CONTROL_TURN_ON
        else:
            type = EVENT_CONTROL_TURN_OFF
        ev = event(vscp_class=CLASS_CONTROL,
                   vscp_type=type,
                   data=struct.pack('>BBB', 0, self.zone, self.subzone))
        await self.updater.send(ev)

    def add_callback(self, callback):
        self.callback.append(callback)

    def get_name(self):
        return self.name

    def get_state(self):
        return self.state

    def is_enabled(self):
        return self.enabled

    def get_group(self):
        return (self.zone, self.subzone)
