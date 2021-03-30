# ZenPacks.daviswr.Aruba.Instant

ZenPack to model & monitor Aruba Instant wireless access points

*Instant On* cloud-managed wireless and Aruba Mobility Controllers are **not** supported.

Tested with IAP-224 APs in Virtual Controller mode with InstantOS 8.6

## Requirements
HPE/Aruba Networks Instant Access Points (not campus APs) with SNMP enabled and accessible from Zenoss.
 * This includes rebranded Aruba equipment from Dell, etc.

## Usage
This ZenPack will add the `/Network/Aruba/Instant` device class, where Virtual Controllers and/or IAPs should be placed.

The modeler will attempt to determine if the monitored device is a Virtual Controller or individual AP (even if a cluster member), but the behavior can be overriden via zProperty.

### zProperties
* `zIapForceController`
  * Denotes that the device should always be modeled as a Virtual Controller, with cluster member APs as components (along with radios & networks)
* `zIapForceStandalone`
  * Denotes that the device should always be modeled as an individual AP, with only its radios and networks as components
* `zWlanApIgnoreNames`
  * Regex of AP names for the modeler to ignore - only applies to Virtual Controllers
* `zWlanApIgnoreModels`
  * List of AP models for the modeler to ignore - only applies to Virtual Controllers
* `zWlanApIgnoreSubnets`
  * List of IP subnets of AP management addresses for the modeler to ignore - only applies to Virtual Controllers
* `zWlanWlanIgnoreNames`
  * Regex of wireless network names for the modeler to ignore
