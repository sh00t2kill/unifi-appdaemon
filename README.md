# unifi-appdaemon
A HA AppDaemon script for unifi ap and switch status


## Config
```
unifi_monitor:
  module: unifi
  class: UnifiAPSW
  user: username
  pass: password
  host: host
  port: port
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
