from zenoss.protocols.protobufs.zep_pb2 import SEVERITY_INFO

# Get attributes from the event object
ap_name = str(getattr(evt, 'wlsxTrapAPLocation.0', ''))
radio = str(getattr(evt, 'wlsxTrapAPRadioNumber.0', ''))
prev_chan = str(getattr(evt, 'wlsxTrapAPPrevChannel.0', ''))
curr_chan = str(getattr(evt, 'wlsxTrapAPRadioNumber.0', ''))
reason = str(getattr(evt, 'wlsxTrapAPARMChangeReason.0', ''))

# Re-model Virtual Controller to get new channel assignment
device.collectDevice(background=True)

if ap_name:
    # AI-AP-MIB::ArubaARMChangeReason
    change_reasons = {
        # radarDetected
        '1': 'radar detected',
        # radarCleared
        '2': 'radar cleared',
        # txHang
        '3': 'transmit hang',
        # txHangCleared
        '4': 'transmit hang cleared',
        # fortyMhzIntol
        '5': 'wide-channel intolerance',
        # cancel40mhzIntol
        '6': 'wide-channel interference cleared',
        # fortMhzAlign
        '7': 'wide-channel alignment',
        # armInterference
        '8': 'interference',
        # armInvalidCh
        '9': 'invalid channel',
        # armErrorThresh
        '10': 'error threshold',
        # armNoiseThreh
        '11': 'noise threshold',
        # armEmptyCh
        '12': 'empty channel',
        # armRogueCont
        '13': 'rogue containment',
        # armDecreasePower
        '14': 'power decrease',
        # armIncreasePower
        '15': 'power increase',
        # armTurnOffRadio
        '16': 'radio turn-off',
        # armTurnOnRadio
        '17': 'radio turn-on',
        }

    # Component
    evt.component = '{0} Radio {1}'.format(ap_name, int(radio) - 1) \
        if radio and radio.isdigit() else ap_name

    # Severity
    evt.severity = SEVERITY_INFO

    # Summary
    evt.summary = 'Channel changed'
    if curr_chan:
        evt.summary += ' to {0}'.format(curr_chan)
    if prev_chan:
        evt.summary += ' from {0}'.format(prev_chan)
    if reason:
        evt.summary += ' due to {0}'.format(change_reasons.get(
            reason,
            'unknown cause'
            ))

else:
    evt._action = 'drop'
