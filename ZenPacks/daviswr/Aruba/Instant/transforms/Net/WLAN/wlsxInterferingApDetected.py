from base64 import b64decode

from zenoss.protocols.protobufs.zep_pb2 import SEVERITY_INFO

# Get attributes from the event object
channel = str(getattr(evt, 'wlsxTrapAPChannel.0', ''))
ssid = str(getattr(evt, 'wlsxTrapTargetAPSSID.0', ''))
ap_name = str(getattr(evt, 'wlsxTrapAPLocation.0', ''))
radio = str(getattr(evt, 'wlsxTrapAPRadioNumber.0', ''))
rogue = str(getattr(evt, 'wlsxTrapTargetAPBSSID.0', ''))

# Rogue AP MAC address
r_mac_addr = ''
if rogue:
    try:
        if rogue.startswith('BASE64:'):
            if not rogue.endswith('=='):
                rogue += '=='
            elif not rogue.endswith('='):
                rogue += '='
            r_mac = b64decode(rogue.replace('BASE64:', ''))
        else:
            r_mac = rogue
        for idx in range(len(r_mac)):
            mac_byte = str(hex(ord(r_mac[idx]))[2:])
            if len(mac_byte) < 2:
                mac_byte = '0' + mac_byte
            r_mac_addr = r_mac_addr + ':' + mac_byte
        r_mac_addr = r_mac_addr[1:]
        if ssid:
            r_mac_addr = ' (' + r_mac_addr + ')'
    except TypeError:
        r_mac_addr = ''

# Component
if ap_name and radio:
    evt.component = '{0} Radio {1}'.format(ap_name, int(radio) - 1)
elif ap_name:
    evt.component = ap_name

# Severity
evt.severity = SEVERITY_INFO

# Summary
evt.summary = 'Interfering AP {0}{1}'.format(
    ssid,
    r_mac_addr if ':' in r_mac_addr else ''
    )
if channel:
    evt.summary += ' on channel {0}'.format(channel)
