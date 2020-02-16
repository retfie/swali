import uvscp
from uvscp_filter import event_filter
from uvscp_event import event
import struct
import time

def read_reg(page, reg, nickname, num=1):
#0x25: ext page read
#0x26: ext page write
#0x27: ext page resp
    if num == 0:
        return bytearray()
    if num == 256:
        num_cmd = 0
    else:
        num_cmd = num

    v = uvscp.vscp()
    #v.set_debuglevel(1)
    v.noop()
    flt = event_filter(0,0,0,0x3ff,0x27,0xFF)
    v.setmask(flt)
    v.setfilter(flt)
    v.clrall()
    v.send(event(vscp_class = 0, vscp_type=0x25, data=struct.pack('>BHBB', nickname, page, reg,num_cmd)))
    time.sleep(0.1)
    resp = v.retr(int(num/4)+2)
    v.quit()
    result=bytearray()
    for item in resp[1]:
        result[item.data[3]:item.data[3]+len(item.data)-4] = item.data[4:]
    return result

def write_reg(page, reg, nickname, value):
    if(len(value) > 4):
        raise ValueError('Register write limited to 4 bytes')
    v = uvscp.vscp()
    #v.set_debuglevel(1)
    v.noop()
    flt = event_filter(0,0,0,0x3ff,0x27,0xFF)
    v.setmask(flt)
    v.setfilter(flt)
    v.clrall()
    v.send(event(vscp_class = 0, vscp_type=0x26, data=struct.pack('>BHB', nickname, page, reg) + value))
    time.sleep(0.1)
    resp = v.retr(1)
    v.quit()

def present(node):
#0x1F: who is there?
#0x20: who is there response
    v = uvscp.vscp()
    #v.set_debuglevel(1)
    v.noop()
    flt = event_filter(0,0,0,0x3ff,0x20,0xFF)
    v.setmask(flt)
    v.setfilter(flt)
    v.clrall()
    v.send(event(vscp_class = 0, vscp_type=0x1F, data=struct.pack('>B', node)))
    time.sleep(0.01)
    resp = v.retr(7)
    v.quit()
    if len(resp[1]) == 7:
        return True
    else:
        return False
