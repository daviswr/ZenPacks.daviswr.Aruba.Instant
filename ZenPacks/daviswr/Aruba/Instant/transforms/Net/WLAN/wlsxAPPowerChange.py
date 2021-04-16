from zenoss.protocols.protobufs.zep_pb2 import SEVERITY_INFO

# Get attributes from the event object
ap_name = str(getattr(evt, 'wlsxTrapAPLocation.0', ''))
radio = str(getattr(evt, 'wlsxTrapAPRadioNumber.0', ''))
prev_power = str(getattr(evt, 'wlsxTrapAPPrevTxPower.0', ''))
curr_power = str(getattr(evt, 'wlsxTrapAPTxPower.0', ''))

if ap_name:
    # Component
    evt.component = ('{0} Radio {1}'.format(ap_name, int(radio) - 1) if radio
                     else ap_name)

    # Severity
    evt.severity = SEVERITY_INFO

    # Summary
    evt.summary = 'Transmit power level changed'
    if curr_power:
        evt.summary += ' to {0}'.format(curr_power)
    if prev_power:
        evt.summary += ' from {0}'.format(prev_power)

else:
    evt._action = 'drop'
