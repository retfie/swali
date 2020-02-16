import asyncio
from .vscp import vscp_tcp
from .const import (DEF_HOST, DEF_PORT, DEF_USER, DEF_PASSWORD)
from .vscp.vscp_util import scan_nodes, read_reg
from .vscp.vscp_tcp import vscp_tcp
from .vscp.vscp_filter import event_filter
from .vscp.vscp_event import event
from .vscp.vscp_guid import guid
from .vscp.const import (CLASS_INFORMATION, EVENT_INFORMATION_ON, EVENT_INFORMATION_OFF)
from .light import light

class gateway:
    """This class connects to the SWALI VSCP Gateway."""
    def __init__(self, host=DEF_HOST, port=DEF_PORT, user=DEF_USER, password=DEF_PASSWORD):
        """Initialize a Gateway object"""
        self._host = host
        self._port = port
        self._user = user
        self._password = password

        self.v = vscp_tcp(host=host, port=port)

    async def _information_update(self, event):
        if event.vscp_type == EVENT_INFORMATION_ON and len(event.data) == 3:
            nick = event.guid.getNickname()
            channel = event.data[0]
            if((nick, channel) in self._lights):
                await self._lights[(nick, channel)].update(True)

        if event.vscp_type == EVENT_INFORMATION_OFF and len(event.data) == 3:
            nick = event.guid.getNickname()
            channel = event.data[0]
            if((nick, channel) in self._lights):
                await self._lights[(nick, channel)].update(False)

    async def connect(self):
        await self.v.connect()

    async def start_update(self):
        await self.v.quitloop()
        flt = event_filter(0,0,CLASS_INFORMATION,0x3ff,0,0x00)
        await self.v.setmask(flt)
        await self.v.setfilter(flt)
        await self.v.clrall()
        await self.v.rcvloop(self._information_update)

    async def stop_update(self):
        await self.v.quitloop()

    async def close(self):
        await self.v.quitloop()
        await self.v.close()

    async def _update_channel(self, nick, channel):
        raw = await read_reg(self.v, nick, channel, 0, num=128)
        if raw[0:2] == b'OU':
            l = light(nick, channel, self.v)
            l.from_raw(raw)
            self._lights[(nick,channel)] = l

        if raw[0:2] == b'IN':
            pass
            #self._switches[(nick,channel)] = switch.from_raw(raw)

    def _update_groups(self):
        self._groups = dict()
        for id, light in self._lights.items():
            if light.is_enabled():
                group = light.get_group()
                if group not in self._groups:
                    self._groups[group] = []
                self._groups[group].append(light)

    async def scan(self):
        """Scan a gateway for SWALI devices and store the state internally"""
        self._lights = dict()
        self._switches = dict()
        self._groups = dict()

        nodes = await scan_nodes(self.v)
        nicknames = [nick for nick, node in nodes.items() if node['stddev']==b'SWALI\0\0\0']

        for nick in nicknames:
            for channel in range(nodes[nick]['pages']):
                await self._update_channel(nick, channel)

        self._update_groups()


    def get_lights(self):
        return [x for k, x in self._lights.items()]

    def get_groups(self):
        return [k for k, x in self._groups.items()]
