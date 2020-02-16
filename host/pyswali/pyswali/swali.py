from uvscp_util import *
import sys
import argparse

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


# Print iterations progress, from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

def scan():
    vscp_nodes = []
    swali_nodes = []
    inputs = []
    outputs = []

    print('Scanning for VSCP nodes')
    for node in range(0, 254):
        printProgressBar(node, 253, length=50)
        if present(node):
            vscp_nodes.append(node)

    print('VSCP nodes')
    print(vscp_nodes)

    for node in vscp_nodes:
        #VSCP_REG_STANDARD_DEVICE_FAMILY_CODE 0x9A
        #VSCP_REG_PAGES_USED                  0x99
        ident = read_reg(0, 0x9A, node, num=8)
        if ident == bytearray(b'SWALI\x00\x00\x00'):
            swali_node = dict()
            swali_node['nickname'] = node
            swali_node['channels'] = int(read_reg(0, 0x99, node)[0])
            for channel in range(0, swali_node['channels']):
                kind = read_reg(channel, 0, int(node), num=2).decode()
                if kind == 'IN':
                    inputs.append((node, channel))
                if kind == 'OU':
                    outputs.append((node, channel))
            swali_nodes.append(node)

    print('SWALI NODES')
    print(swali_nodes)
    print('INPUT CHANNELS')
    print(inputs)
    print('OUTPUT CHANNELS')
    print(outputs)

def conf_output(nickname, channel):
    kind = read_reg(channel, 0, nickname, num=2).decode()
    if kind != 'OU':
        print('channel is not a SWALI output')

    if query_yes_no('Enable output channel?'):
        write_reg(channel, 0x03, nickname, bytearray(b'\x01'))
    else:
        write_reg(channel, 0x03, nickname, bytearray(b'\x00'))
        return

    if query_yes_no('Invert output channel?', default="no"):
        write_reg(channel, 0x07, nickname, bytearray(b'\x01'))
    else:
        write_reg(channel, 0x07, nickname, bytearray(b'\x00'))

    zone = input('Assign to zone?')
    subzone = input('Assign to subzone?')

    data = struct.pack('BB', int(zone), int(subzone))
    write_reg(channel, 0x04, nickname, data)

    minutes = input('Max ontime minutes? (Default = off) ')
    if minutes == '':
        minutes = 0
    else:
        minutes = int(minutes)

    hours = input('Max ontime hours? (Default = off) ')
    if hours == '':
        hours = 0
    else:
        hours = int(hours)

    data = struct.pack('BB', int(hours), int(minutes))
    write_reg(channel, 0x08, nickname, data)

    print('Done!')

def conf_input(nickname, channel):
    kind = read_reg(channel, 0, nickname, num=2).decode()
    if kind != 'IN':
        print('channel is not a SWALI input')

    if query_yes_no('Enable input channel?'):
        write_reg(channel, 0x03, nickname, bytearray(b'\x01'))
    else:
        write_reg(channel, 0x03, nickname, bytearray(b'\x00'))
        return

    if query_yes_no('Invert input channel?', default="no"):
        write_reg(channel, 0x07, nickname, bytearray(b'\x01'))
    else:
        write_reg(channel, 0x07, nickname, bytearray(b'\x00'))

    zone = input('Assign to zone?')
    subzone = input('Assign to subzone?')
    toggle = query_yes_no('Toggle switch? (No = pushbutton)', default="no")

    data = struct.pack('BBB', int(zone), int(subzone), int(toggle))
    write_reg(channel, 0x04, nickname, data)

    print('Done!')

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SWALI configuration")
    parser.add_argument('command', help='scan/output')
    parser.add_argument('-n', '--nick', dest='nickname', default=0x00, help='VSCP Nickname of node (default=0x00)', type=int)
    parser.add_argument('-c', '--channel', dest='channel', default=0x00, help='swali channel of device to configure', type=int)

    args = parser.parse_args()

    if args.command == 'scan':
        scan()

    if args.command == 'output':
        conf_output(args.nickname, args.channel)

    if args.command == 'input':
        conf_input(args.nickname, args.channel)
