server_address = getattr(evt, 'wlsxTrapAuthServerAddress.0', '')
server_name = getattr(evt, 'wlsxTrapAuthServerName.0', '')
user_ip = getattr(evt, 'wlsxTrapUserIpAddress.0', '')
username = getattr(evt, 'wlsxTrapUserName.0', '')

evt.summary = 'Managment user auth failed'

if username:
    evt.summary += ' for {0}'.format(username)

if user_ip:
    evt.summary += ' from {0}'.format(user_ip)

if server_name:
    evt.component = server_name
    evt.summary += ' using {0}'.format(server_name)
    if server_address:
        evt.summary += ' ({0})'.format(server_address)
elif server_address:
    evt.component = server_address
    evt.summary += ' using {0}'.format(server_address)
