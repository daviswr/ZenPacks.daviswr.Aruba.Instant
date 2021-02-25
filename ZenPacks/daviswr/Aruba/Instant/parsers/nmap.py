# pylint: disable=line-too-long,protected-access

from lxml import etree

from Products.ZenRRD.CommandParser import CommandParser
from Products.ZenStatus.nmap.PingResult import PingResult


class nmap(CommandParser):

    def processResults(self, cmd, result):
        """
        Example output - host is up
        <?xml version="1.0"?>
        <?xml-stylesheet href="file:///opt/zenoss/share/nmap/nmap.xsl" type="text/xsl"?>  # noqa
        <!-- Nmap 5.51.4 scan initiated Tue Dec 29 11:27:11 2020 as: /opt/zenoss/bin/nmap -sn -PE -n -&#45;send-ip -&#45;min-rtt-timeout 1.5 -&#45;max-rtt-timeout 1.5 -&#45;max-retries 3 -oX - 192.168.10.3 -->  # noqa
        <nmaprun scanner="nmap" args="/opt/zenoss/bin/nmap -sn -PE -n -&#45;send-ip -&#45;min-rtt-timeout 1.5 -&#45;max-rtt-timeout 1.5 -&#45;max-retries 3 -oX - 192.168.10.3" start="1609259231" startstr="Tue Dec 29 11:27:11 2020" version="5.51.4" xmloutputversion="1.03">  # noqa
        <verbose level="0"/>
        <debugging level="0"/>
        <host><status state="up" reason="echo-reply"/>
        <address addr="192.168.10.3" addrtype="ipv4"/>
        <address addr="18:64:72:C6:E0:B2" addrtype="mac"/>
        <hostnames>
        </hostnames>
        <times srtt="835" rttvar="5000" to="1500000"/>
        </host>
        <runstats><finished time="1609259231" timestr="Tue Dec 29 11:27:11 2020" elapsed="0.04" summary="Nmap done at Tue Dec 29 11:27:11 2020; 1 IP address (1 host up) scanned in 0.04 seconds" exit="success"/><hosts up="1" down="0" total="1"/>  # noqa
        </runstats>
        </nmaprun>

        Example output - host is down
        <?xml version="1.0"?>
        <?xml-stylesheet href="file:///opt/zenoss/share/nmap/nmap.xsl" type="text/xsl"?>  # noqa
        <!-- Nmap 5.51.4 scan initiated Tue Dec 29 11:27:25 2020 as: /opt/zenoss/bin/nmap -sn -PE -n -&#45;send-ip -&#45;min-rtt-timeout 1.5 -&#45;max-rtt-timeout 1.5 -&#45;max-retries 3 -oX - 192.168.10.138 -->  # noqa
        <nmaprun scanner="nmap" args="/opt/zenoss/bin/nmap -sn -PE -n -&#45;send-ip -&#45;min-rtt-timeout 1.5 -&#45;max-rtt-timeout 1.5 -&#45;max-retries 3 -oX - 192.168.10.138" start="1609259245" startstr="Tue Dec 29 11:27:25 2020" version="5.51.4" xmloutputversion="1.03">  # noqa
        <verbose level="0"/>
        <debugging level="0"/>
        <runstats><finished time="1609259248" timestr="Tue Dec 29 11:27:28 2020" elapsed="3.05" summary="Nmap done at Tue Dec 29 11:27:28 2020; 1 IP address (0 hosts up) scanned in 3.05 seconds" exit="success"/><hosts up="0" down="1" total="1"/>  # noqa
        </runstats>
        </nmaprun>
        """

        values = dict()

        # Nmap XML output with CLI parameters from
        # ZenStatus.NmapPingTask._executeNmapCmd()
        parse_tree = etree.fromstring(cmd.result.output)
        host_tree = parse_tree.xpath('/nmaprun/host')
        # host_tree will be an empty list if host is down
        if host_tree:
            ping = PingResult('')
            ping._address = ping._parseAddress(host_tree[0])
            ping._isUp, reason = ping._parseState(host_tree[0])
            ping._rtt, ping._rttVariance = ping._parseTimes(host_tree[0])

            # AP status polling should inform if the AP is down,
            # though the up/clear event may not be reliable.
            # AP up/down traps from the Virtual Controller lack AP name
            # and therefore aren't of much use.
            values['rtt'] = ping.rtt
            values['status'] = 1
        else:
            values['status'] = 2

        for point in cmd.points:
            if point.id in values:
                result.values.append((point, values[point.id]))
