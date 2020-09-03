import curses

from page import Page, PageStyle
from element import Element, Style, Align, Selectable, Link, Break, Wallbreak, Input, Dropdown, Checkbox
from event import KeyEvent

import subprocess
import os
import re
import time
import threading

DEVNULL = open(os.devnull, 'w')

def power_toggle(this, e):
    cmd = f'bluetoothctl power {"off" if get_power() else "on"} | grep "succeeded" | wc -c'
    subprocess.Popen(cmd, shell=True, stdout=DEVNULL)

def get_power():
    cmd = 'bluetoothctl show | grep "Powered: yes" | wc -c'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]

    return not output == b'0\n'

def update_power(this):
    this.text = 'on' if get_power() else 'off'

def poll_devices():
    cmd = 'bluetoothctl devices'
    process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8').split('\n')
    
    return list(filter(lambda s: s != '' and 'Device' in s, output)) 

def grep_info(bd_addr, prop):
    cmd = f'bluetoothctl info {bd_addr} | grep "{prop}" | wc -c'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]

    return not output == b'0\n'

def update_devices(page):
    clear_devices(page)

    for deviceLine in poll_devices():
        deviceElem = Element(
            text=deviceLine,
            classList=['device']
        )

        page.addElement(deviceElem)

def toggle_device_actions(this, e):
    page = this.page

    if this.data.get('display'):
        this.data['display'] = False

        page.removeElements(page.getElementsByClassName(this.ID + 'option'))
    else:
        this.data['display'] = True

        page.addElements(index=this.index() + 1, elements=[
            Selectable(
                text='Pair',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=pair_device
            ) if not grep_info(this.ID, 'Paired: yes') else
            Selectable(
                text='Remove',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=remove_device
            ),
            Selectable(
                text='Connect',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=connect_device
            ) if not grep_info(this.ID, 'Connected: yes') else
            Selectable(
                text='Disconnect',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=disconnect_device
            ),
            Selectable(
                text='Trust',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=trust_device
            ) if not grep_info(this.ID, 'Trusted: yes') else
            Selectable(
                text='Untrust',
                style=Style(
                    indent=2
                ),
                classList=[this.ID + 'option'],
                onselect=untrust_device
            )
        ])

def pair_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])

    this.text = '  Pairing...'
    this.page.cdom.log('Attempting to pair...')

    cmd = f'bluetoothctl pair {bd_addr} | grep "Pairing successful"'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')

    if len(output) > 0:
        this.page.cdom.log(output)
        this.text = '  Pairing successful!'
    else:
        this.text = '  Pairing failed.'
        this.page.cdom.log(output)
    
    threading.Timer(3.0, toggle_twice, [ this.page.getElementByID(bd_addr) ]).start()

def connect_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])

    this.text = '  Connecting...'
    this.page.cdom.log('Attempting to connect...')

    cmd = f'bluetoothctl connect {bd_addr} | grep "Connection successful"'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')

    if len(output) > 0:
        this.page.cdom.log(output)
        this.text = '  Connection succeeded!'
    else:
        this.text = '  Connection attempt failed.'
        this.page.cdom.log(output)
    
    threading.Timer(3.0, toggle_twice, [ this.page.getElementByID(bd_addr) ]).start()

def disconnect_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])

    this.text = '  Disconnecting...'
    this.page.cdom.log('Attempting to disconnect...')

    cmd = f'bluetoothctl disconnect {bd_addr} | grep "Successful disconnected"'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')

    if len(output) > 0:
        this.text = '  Disconnection succeeded!'
    else:
        this.text = '  Disconnection attempt failed.'

    this.page.cdom.log(output)
    
    threading.Timer(3.0, toggle_twice, [ this.page.getElementByID(bd_addr) ]).start()

# yes this is stupid but do i care

def toggle_twice(this):
    toggle_device_actions(this, None)
    toggle_device_actions(this, None)
    # no

def trust_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])

    cmd = f'bluetoothctl trust {bd_addr} | grep "trust succeeded"'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')

    if len(output) > 0:
        this.page.cdom.log(output)
    
    threading.Timer(1.0, toggle_twice, [ this.page.getElementByID(bd_addr) ]).start()

def untrust_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])

    cmd = f'bluetoothctl untrust {bd_addr} | grep "untrust succeeded"'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8')

    if len(output) > 0:
        this.page.cdom.log(output)
    
    threading.Timer(1.0, toggle_twice, [ this.page.getElementByID(bd_addr) ]).start()

def reset_text_and_log(this, text):
    this.text = text
    this.page.cdom.log('')

def load_devices(page):
    for deviceLine in poll_devices():
        deviceElem = Selectable(
            text=deviceLine,
            style=Style(
                indent=1
            ),
            classList=['device'],
            ID=bd_addr_from_line(deviceLine),
            onselect=toggle_device_actions
        )

        page.addElement(deviceElem)

def clear_devices(page):
    page.removeElements(page.getElementsByClassName('device'))

def remove_device(this):
    bd_addr = bd_addr_from_line(this.classList[0])
    deviceElem = this.page.getElementByID(bd_addr)

    cmd = f'bluetoothctl remove {bd_addr} | grep "not available" | wc -c'
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]

    if output:
        toggle_device_actions(deviceElem, None)

        if bd_addr in found_addrs:
            found_addrs.remove(bd_addr)

        this.page.removeElement(deviceElem)

def bd_addr_from_line(line: str):
    search = re.search(r'(?:[0-9a-fA-F]:?){12}', line)

    return search.group() if search is not None else ''

found_addrs = []

scan_step = 0
scanTitles = [
    'Scanning   ',
    'Scanning.  ',
    'Scanning.. ',
    'Scanning...'
]

def show_scanned_devices(page):
    global scan_step

    if scan_step % 6 == 0:
        if scanTitles.index(page.title) == len(scanTitles) - 1:
            page.title = scanTitles[0]
        else:
            page.title = scanTitles[scanTitles.index(page.title) + 1]
    
    scan_step += 1

    page.getElementByID('scan-error').text = ''

    if not get_power():
        page.getElementByID('scan-error').text = 'Power is off'
        return

    for deviceLine in poll_devices():
        bd_addr = bd_addr_from_line(deviceLine)

        if not bd_addr in found_addrs and bd_addr != '':
            device = Selectable(
                text=' ' + deviceLine,
                classList=['device'],
                ID=bd_addr,
                onselect=toggle_device_actions
            )

            page.addElement(device)

            found_addrs.append(bd_addr)

scan_process = None

def start_scan(page):
    global scan_process, found_addrs

    found_addrs = list(map(bd_addr_from_line, poll_devices()))

    clear_devices(page)

    scan_process = subprocess.Popen('bluetoothctl agent on'.split(' '), stdout=DEVNULL, stderr=DEVNULL)
    scan_process = subprocess.Popen('bluetoothctl scan on'.split(' '), stdout=DEVNULL, stderr=DEVNULL)
    
def stop_scan(page):
    scan_process.kill()
    
    subprocess.Popen('bluetoothctl scan off'.split(' '), stdout=DEVNULL, stderr=DEVNULL)
    subprocess.Popen('bluetoothctl agent off'.split(' '), stdout=DEVNULL, stderr=DEVNULL)

def stop_and_exit(this, e):
    if scan_process is not None:
        scan_process.kill()
    exit()

pages = [
    Page(
        url='home',
        title='Bluetoothctl TUI',
        size=(10, 40),
        elements=[
            Break(),
            Selectable(
                text='Toggle Power',
                onselect=power_toggle
            ),
            Element(
                text='on',
                style=Style(
                    align=Align.RIGHT
                ),
                onload=update_power,
                onrefresh=update_power
            ),
            Link(
                label='Device Properties',
                url='devlist'
            ),
            Link(
                label='Scan for Devices',
                url='scan'
            ),
            Break(),
            Selectable(
                text='Quit',
                onselect=stop_and_exit
            )
        ],
        stateless=False
    ),
    Page(
        url='devlist',
        title='Device Properties',
        size=(None, None),
        elements=[
            Element(
                text='Devices:',
                style=Style(
                    weight=curses.A_BOLD
                )
            )
        ],
        onload=load_devices
    ),
    Page(
        url='scan',
        title='Scanning...',
        size=(None, None),
        elements=[
            Element('Select a device to pair, trust, and connect to it'),
            Element(
                text='',
                style=Style(
                    weight=curses.A_BOLD
                ),
                ID='scan-error'
            ),
            Element(
                text='Devices:',
                style=Style(
                    weight=curses.A_BOLD
                )
            )
        ],
        onload=start_scan,
        onunload=stop_scan,
        onrefresh=show_scanned_devices
    )
]