from pyunifi.controller import Controller, APIError
import json
import re
import hassapi as hass
import datetime

class UnifiAPSW(hass.Hass):

    def initialize(self):

        self.username = self.args['user']
        self.password = self.args['pass']
        self.host     = self.args['host']
        self.port     = self.args['port']
        if 'site_id' in self.args:
            self.site_id = self.args['site_id']
        else:
            self.site_id = 'default'
        self.client = self.get_login_client()

        self.log("Unifi AP and Switches Started")
        self.log("Logging in to Unifi Controller")
        if "aps" in self.args:
            self.run_in(self.update_aps, 0)
            self.run_every(self.update_aps, datetime.datetime.now(), 60)
        if "switches" in self.args:
            self.run_in(self.update_switches, 0)
            self.run_every(self.update_switches, datetime.datetime.now(), 60)
        if "gateway_mac" in self.args:
            self.run_in(self.update_health, 0)
            self.run_every(self.update_health, datetime.datetime.now(), 60)
            self.run_in(self.update_wan, 0)
            self.run_every(self.update_wan, datetime.datetime.now(), 60)

        self.listen_event(self.unifi_update_event, "UNIFI_UPDATE")
        self.run_every(self.login_client,  datetime.datetime.now(), 1200)

    def login_client(self, kwargs):
        self.client = self.get_login_client()

    def get_login_client(self):
        try:
            client = Controller(self.host, self.username, self.password, self.port, 'UDMP-unifiOS', site_id=self.site_id, ssl_verify=False)
        except APIError:
            client = Controller(self.host, self.username, self.password, self.port, 'v6', site_id=self.site_id, ssl_verify=False)
        return client


    def unifi_update_event(self, UNIFI_UPDATE, data, kvargs):
        self.run_in(self.update_aps, 0)
        self.run_in(self.update_switches, 0)

    def update_wan(self, kwards):
        if "gateway_mac" not in self.args:
            return None
        self.log("Updating WAN stats")
        gw = self.client.get_device_stat(self.args["gateway_mac"])
        entity = "sensor.unifi_gw_"
        uplink = gw["uplink"]["ip"]
        latency = gw["uplink"]["latency"]
        self.set_state(entity + "uplink_ip", state = uplink, friendly_name = "Uplink IP Address")
        self.set_state(entity + "uplink_latency", state = latency, friendly_name = "Uplink Latency", unit_of_measurement = "s")
        wan_stats = {
            "wan_rxp": gw["stat"]["gw"]["wan-rx_packets"],
            "wan_txp": gw["stat"]["gw"]["wan-tx_packets"],
            "wan_rxb": gw["stat"]["gw"]["wan-rx_bytes"],
            "wan_txb": gw["stat"]["gw"]["wan-tx_bytes"],
        }
        for key, value in wan_stats.items():
            self.set_state(entity + key, state = value, friendly_name = key.replace("_", " ").title(), unit_of_measurement = key[-1])
            if key[-1] == "b":
                # We have a measurement in bytes, lets add a new one for MB
                bytes = value
                mb_value = round(bytes / 1048576, 2)
                new_name = key.replace("xb","xmb")
                current_state = self.get_state(entity + new_name)
                self.set_state(entity + new_name, state = mb_value, friendly_name = new_name.replace("_", " ").title(), unit_of_measurement = "MB")

                if current_state and float(current_state) > 0:
                    # convert bytes/min to megabits/second
                    diff_mb = mb_value - float(current_state)
                    mbps = round(diff_mb * 0.133333, 2)
                    mbps_name = key.replace("xb", "xmbps")
                    self.set_state(entity + mbps_name, state=mbps, friendly_name = mbps_name.replace("_", " ").title(), unit_of_measurement = "Mbps")


    def update_aps(self, kwargs):
        self.log("Update APs Started")
        for ap in self.args['aps']:
            entity = "sensor.unifi_" + ap['name'] + "_ap"
            stat = self.client.get_sysinfo()
            devs = self.client.get_device_stat(ap['mac'])
            self.set_state(entity + "_ip", state = devs['ip'], friendly_name = ap['name'].title() + " IP Address")
            clients = self.client.get_clients()
            numclients = int(devs['user-wlan-num_sta'])
            self.set_state(entity + "_clients", state = numclients, friendly_name = ap['name'].title() + " AP Clients", unit_of_measurement = "Clients")
            numguests = int(devs['guest-wlan-num_sta'])
            self.set_state(entity + "_guests", state = numguests, friendly_name = ap['name'].title() + " AP Guests", unit_of_measurement = "Guests")
            score = int(devs['satisfaction'])
            self.set_state(entity + "_score", state = score, friendly_name = ap['name'].title() + " AP Score", unit_of_measurement = "%" )
            update = devs['upgradable']
            self.set_state("binary_sensor.unifi_" + ap['name'] + "_ap_update", state = update, friendly_name = ap['name'].title() + " AP Update", device_class="update" )
            cpu = float(devs['system-stats']['cpu'])
            self.set_state(entity + "_cpu", state = cpu, friendly_name = ap['name'].title() + " AP CPU", unit_of_measurement = "%")
            ram = float(devs['system-stats']['mem'])
            self.set_state(entity + "_ram", state = ram, friendly_name = ap['name'].title() + " AP RAM", unit_of_measurement = "%")
            activity = round(devs['uplink']['rx_bytes-r']/125000 + devs['uplink']['tx_bytes-r']/125000,1)
            self.set_state(entity + "_activity", state = activity, friendly_name = ap['name'].title() + " AP Activity")
            seconds = devs['uptime']
            days = seconds // 86400
            hours = (seconds - (days * 86400)) // 3600
            minutes = (seconds - (days * 86400) - (hours * 3600)) // 60
            uptime = str(days)+'d '+str(hours)+'h '+str(minutes)+'m'
            self.set_state(entity + "_uptime", state = uptime, friendly_name = ap['name'].title() + " AP Uptime")
            wifi0clients = int(devs['radio_table_stats'][0]['user-num_sta'])
            self.set_state(entity + "_2_4ghz_clients", state = wifi0clients, friendly_name = ap['name'].title() + " AP 2.4GHz Clients", unit_of_measurement = "Clients")
            wifi1clients = int(devs['radio_table_stats'][1]['user-num_sta'])
            self.set_state(entity + "_5ghz_clients", state = wifi1clients, friendly_name = ap['name'].title() + " AP 5GHz Clients", unit_of_measurement = "Clients")
            self.log(entity)
            self.set_state(entity, state = numclients, attributes = {"Clients":numclients, "Guests":numguests, "Clients_wifi0":wifi0clients, "Clients_wifi1":wifi1clients, "Score":score, "CPU":str(cpu), "RAM":str(ram), "Uptime":uptime, "Activity":str(activity)+' Mbps', "Update":update})

    def update_switches(self, kwargs):
        self.log("Update Switches Started")
        for switch in self.args['switches']:
            entity = "sensor.unifi_" + switch['name']
            devs = self.client.get_device_stat(switch['mac'])
            model = devs['model']
            self.log('Switch Model: ' + model + " : " + devs['ip'])
            self.set_state(entity + "_ip", state = devs['ip'], friendly_name = switch['name'].title() + " IP Address")
            for x in range(len(devs['port_table'])):
                port = devs['port_table'][x]
                port_poe = port['port_poe']
                port_name = port['name']
                if port_poe == True:
                    poe_power = round(float(devs['port_table'][x]['poe_power']), 1)
                    poe_voltage = round(float(devs['port_table'][x]['poe_voltage']))
                    self.log(str(switch['name']) + ' Port ' + str(x+1) + ' ' + str(port_name) + ': ' + str(poe_power) + 'W' + ' ' + str(poe_voltage) + 'V')
                    self.set_state(entity + "_port" + str(x+1) + "_power", state = poe_power, attributes = {"friendly_name": port_name, "device_class": "power", "unit_of_measurement": "W", "model": model})
                    self.set_state(entity + "_port" + str(x+1) + "_voltage", state = poe_voltage, attributes = {"friendly_name": port_name, "device_class": "voltage", "unit_of_measurement": "V", "model": model})

                port_link_state = "on" if port['up'] == True else "off"
                port_speed = port['speed']
                self.log(str(switch['name']) + ' Port ' + str(x+1) + ' ' + str(port_name) + " is " + str(port_link_state))
                self.set_state("binary_" + entity + "_port" + str(x+1) + "_link", state = port_link_state, attributes = {"friendly_name": port_name, "device_class": "connectivity", "model": model})
                self.set_state(entity + "_port" + str(x+1) + "_speed", state = port_speed, attributes = {"friendly_name": port_name, "device_class": "connectivity", "unit_of_measurement": "Mbps", "model": model})

    def update_health(self, kwargs):
        if "gateway_mac" not in self.args:
            return None
        self.log("Update Health Started")
        target_mac = self.args["gateway_mac"]
        health = self.client.get_healthinfo()
        wirelessclients = int(health[0]['num_user'])
        wiredclients = int(health[3]['num_user'])
        isp_upload = int(health[2]['xput_up'])
        isp_download = int(health[2]['xput_down'])
        udm_memory = health[1]['gw_system-stats']['mem']
        udm_cpu = health[1]['gw_system-stats']['cpu']
        self.set_state("sensor.unifi_gw_num_wireless_clients", state = wirelessclients, attributes = {"friendly_name": "Unifi Wireless Clients", "unit_of_measurement": "Clients", "icon": "mdi:access-point"})
        self.set_state("sensor.unifi_gw_num_wired_clients", state = wiredclients, attributes = {"friendly_name": "Unifi Wired Clients", "unit_of_measurement": "Clients", "icon": "mdi:lan-connect"})
        self.set_state("sensor.unifi_gw_isp_up", state = isp_upload, attributes = {"friendly_name": "Unifi ISP Upload", "unit_of_measurement": "Mbps", "icon": "mdi:upload"})
        self.set_state("sensor.unifi_gw_isp_down", state = isp_download, attributes = {"friendly_name": "Unifi ISP Download", "unit_of_measurement": "Mbps", "icon": "mdi:download"})
        self.set_state("sensor.unifi_gw_mem", state = udm_memory, attributes = {"friendly_name": "Unifi Memory", "unit_of_measurement": "%", "icon": "mdi:memory"})
        self.set_state("sensor.unifi_gw_cpu", state = udm_cpu, attributes = {"friendly_name": "Unifi CPU", "unit_of_measurement": "%", "icon": "mdi:cpu-64-bit"})
        self.log("Update Health Complete")
