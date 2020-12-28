from zenoss.protocols.protobufs.zep_pb2 import (
    SEVERITY_CLEAR,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL
    )

current = int(float(evt.current))

if evt.eventKey.endswith('Status'):
    if 'aiSSIDStatus' in evt.eventKey:
        status_booleans = {
            0: True,
            1: False,
            }
        status_strings = {
            0: 'enabled',
            1: 'disabled',
            }
        severities = {
            0: SEVERITY_CLEAR,
            1: SEVERITY_WARNING,
            }
    else:
        status_booleans = {
            1: True,
            2: False,
            }
        status_strings = {
            1: 'up',
            2: 'down',
            }
        severities = {
            1: SEVERITY_CLEAR,
            2: SEVERITY_CRITICAL
            }

    if component and hasattr(component, 'enabled'):
        @transact
        def updateDb():
            component.enabled = status_booleans.get(current, False)
        updateDb()

    status_str = status_strings.get(current, 'unknown')
    comp_name = component.title if component and component.title \
        else evt.component

    evt.summary = '{0} is {1}'.format(comp_name, status_str)
    evt.severity = severities.get(current, SEVERITY_WARNING)
    evt.eventClass = '/Status'
