# pylint: disable=line-too-long,invalid-name

__doc__ = """ArubaInstant
gathers OS and hardware information from an Aruba Instant virtual controller
"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin import (
    GetMap,
    GetTableMap,
    SnmpPlugin
    )
from Products.DataCollector.plugins.DataMaps import (
    MultiArgs,
    ObjectMap,
    RelationshipMap
    )


class ArubaInstant(SnmpPlugin):
    """ Aruba Instant Access Point SNMP modeler """
    maptype = 'ArubaInstant'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanApIgnoreNames',
        'zWlanApIgnoreSubnets',
        'zWlanApIgnoreModels',
        'zWlanWlanIgnoreNames',
        'zIapForceController',
        'zIapForceStandalone',
        )

    aiWlanSSIDEntry = {
        # aiSSID
        '.2': 'title',
        # aiSSIDStatus
        '.3': 'enabled',
        # aiSSIDHide
        '.5': 'broadcast',
        }

    aiAccessPointEntry = {
        # aiAPMACAddress
        '.1': 'mac',
        # aiAPName
        '.2': 'title',
        # aiAPIPAddress
        '.3': 'ip',
        # aiAPSerialNum
        '.4': 'serial',
        # aiAPModelName
        '.6': 'model',
        # aiAPTotalMemory
        '.10': 'totalMemory',
        # aiAPStatus
        '.11': 'enabled',
        # aiAPRole,
        '.13': 'role',
        }

    aiRadioEntry = {
        # aiRadioMACAddress
        '.3': 'mac',
        # aiRadioChannel
        '.4': 'channel',
        # aiRadioStatus
        '.20': 'enabled',
        # aiRadioMode
        '.22': 'mode',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'aiWlanSSIDTable',
            '.1.3.6.1.4.1.14823.2.3.3.1.1.7.1',
            aiWlanSSIDEntry
            ),
        GetTableMap(
            'aiAccessPointTable',
            '.1.3.6.1.4.1.14823.2.3.3.1.2.1.1',
            aiAccessPointEntry
            ),
        GetTableMap(
            'aiRadioTable',
            '.1.3.6.1.4.1.14823.2.3.3.1.2.2.1',
            aiRadioEntry
            ),
        )

    snmpGetMap = GetMap({
        # AI-AP-MIB::aiVirtualControllerName.0
        '.1.3.6.1.4.1.14823.2.3.3.1.1.2.0': 'vcName',
        # AI-AP-MIB::aiVirtualControllerVersion.0
        '.1.3.6.1.4.1.14823.2.3.3.1.1.4.0': 'version',
        # AI-AP-MIB::aiVirtualControllerIPAddress.0
        '.1.3.6.1.4.1.14823.2.3.3.1.1.5.0': 'vcMgmtIP',
        # AI-AP-MIB::aiMasterIPAddress.0
        '.1.3.6.1.4.1.14823.2.3.3.1.1.6.0': 'vcRoleAP',
        # SNMPv2-MIB::sysDescr.0
        '.1.3.6.1.2.1.1.1.0': 'sysDescr',
        })

    @staticmethod
    def ip_in_nets(ip, nets):
        """Determines if an IP address is in a subnet in a list"""
        contains = False
        for net in nets:
            try:
                if net.Contains(ipaddr.IPAddress(ip)):
                    contains = True
                    break
            except ValueError:
                break
        return contains

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        if not getdata:
            log.warn(
                'Unable to get data from AI-AP-MIB on %s - skipping model',
                device.id
                )
            return None

        log.debug('SNMP Tables:\n%s', tabledata)

        aiAccessPointTable = tabledata.get('aiAccessPointTable')
        log.debug('aiAccessPointTable has %s entries', len(aiAccessPointTable))

        aiRadioTable = tabledata.get('aiRadioTable')
        log.debug('aiRadioTable has %s entries', len(aiRadioTable))

        aiWlanSSIDTable = tabledata.get('aiWlanSSIDTable')
        log.debug('aiWlanSSIDTable has %s entries', len(aiWlanSSIDTable))

        manufacturer = 'Aruba Networks'
        os = 'InstantOS'
        sys_ver = ''

        # Example:
        # ArubaOS (MODEL: 224), Version 8.6.0.6-8.6.0.6
        sysdescr_re = r'.+ (.+)\),? Version (.+)'
        match = re.match(sysdescr_re, getdata.get('sysDescr', ''))
        if match:
            (getdata['model'], sys_ver) = match.groups()

        sw_version = getdata.get('version', sys_ver)
        os = ('{0} {1}'.format(os, sw_version.split('-')[0]) if sw_version
              else os)
        getdata['setOSProductKey'] = MultiArgs(os, manufacturer)

        vc_ap = getdata.get('vcRoleAP', '')
        mgmt_ip = getdata.get('vcMgmtIP', '')

        force_controller = getattr(device, 'zIapForceController', False)
        force_standalone = getattr(device, 'zIapForceStandalone', False)

        # These are mutually-exclusive and if both are on, same as both off
        if force_controller and force_standalone:
            force_controller = False
            force_standalone = False

        if force_controller:
            getdata['standalone'] = False
        elif force_standalone:
            getdata['standalone'] = True
        else:
            # Determine if Virtual Controller or standalone AP
            if (device.manageIp == mgmt_ip
                    or (device.manageIp == vc_ap and not mgmt_ip)):
                getdata['standalone'] = False
            else:
                getdata['standalone'] = True

        use_case = ('an individual InstantAP' if getdata['standalone']
                    else 'a Virtual Controller')
        log.info('Modeling %s as %s', device.id, use_case)

        # Can't assemble the ObjectMap yet, have to find VC AP in AP table

        # Ignore criteria
        ignore_model_list = getattr(device, 'zWlanApIgnoreModels', list())
        if ignore_model_list:
            log.info(
                'zWlanApIgnoreModels set to %s',
                str(ignore_model_list)
                )

        ignore_ap_regex = getattr(device, 'zWlanApIgnoreNames', '')
        if ignore_ap_regex:
            log.info('zWlanApIgnoreNames set to %s', ignore_ap_regex)

        ignore_net_text = getattr(device, 'zWlanApIgnoreSubnets', list())
        ignore_nets = list()
        if ignore_net_text:
            log.info(
                'zWlanApIgnoreSubnets set to %s',
                str(ignore_net_text)
                )
            for net in ignore_net_text:
                try:
                    ignore_nets.append(ipaddr.IPNetwork(net))
                except ValueError:
                    log.warn('%s is not a valid CIDR address', net)
                    continue

        ignore_names_regex = getattr(device, 'zWlanWlanIgnoreNames', '')
        if ignore_names_regex:
            log.info('zWlanWlanIgnoreNames set to %s', ignore_names_regex)

        # Access Points
        aps = dict()
        ap_radios = dict()

         # Clean up some values
        attr_map = dict()
        attr_map['enabled'] = {
            1: True,
            2: False,
            }

        attr_map['role'] = {
            'cluster slave': 'Cluster AP',
            'cluster master': 'Virtual Controller',
            }

        for snmpindex in aiAccessPointTable:
            row = aiAccessPointTable[snmpindex]
            name = row.get('title', None)
            model = row.get('model', '')
            ip = row.get('ip', '')
            role = row.get('role', '')

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            if 'mac' in row:
                row['mac'] = self.asmac(row['mac'])

            row['snmpindex'] = snmpindex.strip('.')

            # Ignore checks
            if (ip == vc_ap
                    or ip == device.manageIp
                    or 'cluster' not in role.lower()
                    or len(aiAccessPointTable) == 1):
                log.debug('Skipping ignore checks for AP being modeled')
                # Make this AP's info available as the Device
                getdata.update(row)
            elif getdata.get('standalone', False) and ip != device.manageIp:
                log.debug('Standalone model forced, skipping cluster members')
                continue
            elif not name:
                continue
            elif ignore_ap_regex and re.search(ignore_ap_regex, name):
                log.debug('Skipping AP %s due to zWlanApIgnoreNames', name)
                continue
            elif model in ignore_model_list:
                log.debug('Skipping AP %s due to zWlanApIgnoreModels', name)
                continue
            elif self.ip_in_nets(ip, ignore_nets):
                log.debug('Skipping AP due to zWlanApIgnoreSubnets', name)
                continue

            log.debug('Found AP: %s', name)
            aps[name] = row
            ap_radios[row['snmpindex']] = dict()

        # Access Point Radios
        width_map = {
            '+': 40,
            'E': 80,
            'S': 160,
            }

        for snmpindex in aiRadioTable:
            row = aiRadioTable[snmpindex]
            ap_index = '.'.join(snmpindex.split('.')[:-1]).strip('.')
            radio_index = snmpindex.replace(ap_index, '').strip('.')

            if ap_index in ap_radios:
                # Enabled/disable value is the same as APs
                for attr in attr_map:
                    if attr in row:
                        row[attr] = attr_map[attr].get(row[attr], row[attr])

                channel = row.get('channel', '')
                width_code = channel[-1]
                row['width'] = '{0} MHz'.format(width_map.get(width_code, 20))
                row['channel'] = (channel[:-1] if width_code in width_map
                                  else channel)

                row['band'] = 'Unknown'
                row['band_short'] = '?'
                if row['channel'].isdigit():
                    if int(row['channel']) in range(1, 15):
                        row['band'] = '2.4 GHz'
                    elif int(row['channel']) in range(32, 174):
                        row['band'] = '5 GHz'
                    row['band_short'] = row['band'].replace(' GHz', '')

                if 'mac' in row:
                    row['mac'] = self.asmac(row['mac'])

                if 'mode' in row:
                    row['mode'] = row['mode'].title()

                log.debug(
                    'Found radio %s for AP index %s',
                    radio_index,
                    ap_index
                    )
                row['snmpindex'] = snmpindex.strip('.')
                ap_radios[ap_index][radio_index] = row

        # Wireless Networks
        wlan_list = list()
        for snmpindex in aiWlanSSIDTable:
            row = aiWlanSSIDTable[snmpindex]
            name = row.get('title', None)

            if not name:
                continue
            elif ignore_names_regex and re.search(ignore_names_regex, name):
                log.debug(
                    'Skipping WLAN %s due to zWlanWlanIgnoreNames',
                    name
                    )
                continue

            log.debug('Found WLAN: %s', name)

            # Clean up attributes
            for attr in ['broadcast', 'enabled']:
                if attr in row:
                    row[attr] = True if 0 == row[attr] else False

            row['id'] = self.prepId(name)
            row['snmpindex'] = snmpindex.strip('.')
            wlan_list.append(row)

        # Build Relationship Maps
        getdata['setHWProductKey'] = MultiArgs(
            getdata.get('model'),
            manufacturer
            )
        getdata['setHWSerialNumber'] = getdata.get('serial', '')
        # Prevent Virtual Controller device from
        # getting title of its self-AP component
        if 'title' in getdata:
            del getdata['title']

        maps.append(ObjectMap(
            modname='ZenPacks.daviswr.Aruba.Instant.VirtualController',
            data=getdata
            ))
        if getdata.get('totalMemory', None):
            maps.append(ObjectMap(
                {'totalMemory': getdata['totalMemory']},
                compname='hw'
                ))

        wlan_rm = RelationshipMap(
            relname='iapNetworks',
            modname='ZenPacks.daviswr.Aruba.Instant.InstantNetwork'
            )
        for wlan in wlan_list:
            wlan_rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Aruba.Instant.InstantNetwork',
                data=wlan
                ))
        maps.append(wlan_rm)

        ap_rm = RelationshipMap(
            relname='clusterIAPs',
            modname='ZenPacks.daviswr.Aruba.Instant.InstantAP'
            )

        standalone_radio_rm = RelationshipMap(
            relname='iapRadios',
            modname='ZenPacks.daviswr.Aruba.Instant.InstantRadio'
            )

        # Model as standalone AP - Only radios as components
        if getdata.get('standalone', False):
            ap = getdata

            for radio_index in ap_radios[ap['snmpindex']]:
                radio = ap_radios[ap['snmpindex']][radio_index]
                radio['id'] = self.prepId('Radio_{0}'.format(radio_index))
                radio['title'] = 'Radio {0}'.format(radio_index)
                standalone_radio_rm.append(ObjectMap(
                    modname='ZenPacks.daviswr.Aruba.Instant.InstantRadio',
                    data=radio
                    ))
            maps.append(standalone_radio_rm)
            # Need empty AP RelMap to remove lingering APs
            # if previously modeled as a Controller
            maps.append(ap_rm)

        # Model as Virtual Controller - APs as components
        else:
            radio_rm_list = list()

            for ap_name in aps:
                ap = aps[ap_name]
                ap['id'] = self.prepId(ap_name)
                ap_rm.append(ObjectMap(
                    modname='ZenPacks.daviswr.Aruba.Instant.InstantAP',  # noqa
                    data=aps[ap_name]
                    ))

                radio_rm = RelationshipMap(
                    compname='clusterIAPs/{0}'.format(ap['id']),
                    relname='iapRadios',
                    modname='ZenPacks.daviswr.Aruba.Instant.InstantRadio'
                    )

                for radio_index in ap_radios[ap['snmpindex']]:
                    radio = ap_radios[ap['snmpindex']][radio_index]
                    radio['id'] = self.prepId('{0}_{1}'.format(
                        ap['id'],
                        radio_index
                        ))
                    radio['title'] = '{0} Radio {1}'.format(
                        ap_name,
                        radio_index
                        )
                    radio_rm.append(ObjectMap(
                        modname='ZenPacks.daviswr.Aruba.Instant.InstantRadio',  # noqa
                        data=radio
                        ))
                # Append this AP's radio RelMap
                radio_rm_list.append(radio_rm)
            maps.append(ap_rm)
            maps += radio_rm_list
            # Need empty Radio RelMap to remove lingering Radios
            # if previously modeled as a standalone AP
            maps.append(standalone_radio_rm)

        log.debug('%s RelMaps:\n%s', self.name(), str(maps))

        return maps
