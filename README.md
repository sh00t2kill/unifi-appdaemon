# unifi-appdaemon
A HA AppDaemon script for unifi ap and switch status

### Big ups to Holdestmade from the HA community forum who put the initial script together. I just converted it into something that has Appdaemon configuration rather than hard coded adresses and devices

## Config
in apps.yaml
```
unifi_monitor:
  module: unifi
  class: UnifiAPSW
  user: username
  pass: password
  host: host
  port: port
  gateway_mac: <mac of usg/udmp>
  aps:
    - name: name_of_ap1
      mac: xx:xx:xx:xx:xx:xx
    - name: name_of_ap1
      mac: xx:xx:xx:xx:xx:xx
  switches:
    - name: swtich1
      mac: xx:xx:xx:xx:xx:xx
    - name: switch2
      mac: xx:xx:xx:xx:xx:xx
```
Note, appdaemon config will need to have pyunifi added as a python module


For every AP configured:

Create sensor for number of connected clients

Create sensor for number of guest clients

Create sensor for Unifi AP score

Create binary_sensor if an update is outstanding

Create sensor for CPU

Create sensor for ram

Create sensor for activity

Create sensor for uptime

Create sensors for 2.4/5ghz connected clients


For every switch configured

Create binary_sensor for connected or not

Create sensor for link speed

If switch port is POE, create sensors for port voltage and power
