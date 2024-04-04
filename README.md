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


For every AP configured:<br>
<ul>
<li>Create sensor for number of connected clients</li>
<li>Create sensor for number of guest clients</li>
<li>Create sensor for Unifi AP score</li>
<li>Create binary_sensor if an update is outstanding</li>
<li>Create sensor for CPU</li>
<li>Create sensor for ram</li>
<li>Create sensor for activity</li>
<li>Create sensor for uptime</li>
<li>Create sensors for 2.4/5ghz connected clients</li>
</ul>

For every switch configured:<br>
<ul>
<li>Create binary_sensor for connected or not</li>
<li>Create sensor for link speed</li>
<li>If switch port is POE, create sensors for port voltage and power</li>
</ul>
For the configured gateway, some health stats and WAN usage sensors are created.<br>
<ul>
<li>wireless clients
<li>wired clients</li>
<li>isp up</li>
<li>isp down</li>
<li>memory</li>
<li>cpu</li>
<li>wan-rx bytes</li>
<li>wan-rx MB</li>
<li>wan-tx bytes</li>
<li>wan-tx MB</li>
</ul>

Note, `gateway_mac`, `switches` and `aps` are all optional. If the config option isnt set, the relevant functions do not run and sensors are not created or updated.
