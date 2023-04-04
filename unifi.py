from pyunifi.controller import Controller
import json
import re
import hassapi as hass
import datetime

class UnifiAPSW(hass.Hass):

    def initialize(self):
        self.log("Unifi AP and Switches Started")
        self.run_in(self.update_aps, 0)
        self.run_every(self.update_aps, datetime.datetime.now(), 600)
        self.run_in(self.update_switches, 0)
        self.run_every(self.update_switches, datetime.datetime.now(), 600)
        self.listen_event(self.unifi_update_event, "UNIFI_UPDATE")

        self.username = self.args['user']
        self.password = self.args['pass']
        self.host     = self.args['host']
        self.port     = self.args['port']

    def unifi_update_event(self, UNIFI_UPDATE, data, kvargs):
        self.run_in(self.update_aps, 0)
        self.run_in(self.update_switches, 0)

    def update_aps(self, kwargs):
        self.log("Update APs Started")
        for ap in self.args['aps']:
            entity = "sensor.unifi_" + ap['name'] + "_ap"
            client = Controller(self.host, self.username, self.password, self.port, 'v6', site_id='default', ssl_verify=False)
            stat = client.get_sysinfo()
            devs = client.get_device_stat(ap['mac'])
            #self.log(devs)
            clients = client.get_clients()
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
            model = devs['model']
            if model == 'UAL6':
                picture = "/local/images/unifiap62.png"
            elif model == 'U7IW':
                picture = "/local/images/unifiapiw2.png"
            elif model == 'UHDIW':
                picture = "/local/images/unifiapiw2.png"
            else:
                picture = "/local/images/unifiap62.png"
            self.set_state(entity, state = numclients, attributes = {"entity_picture":picture, "Clients":numclients, "Guests":numguests, "Clients_wifi0":wifi0clients, "Clients_wifi1":wifi1clients, "Score":score, "CPU":str(cpu), "RAM":str(ram), "Uptime":uptime, "Activity":str(activity)+' Mbps', "Update":update})

    def update_switches(self, kwargs):
        self.log("Update Switches Started")
        for switch in self.args['switches']:
            entity = "sensor.unifi_" + switch['name']
            client = Controller(self.host, self.username, self.password, self.port, 'v6', site_id='default', ssl_verify=False)
            devs = client.get_device_stat(switch['mac'])
            model = devs['model']
            self.log('Switch Model: ' + model)
            for x in range(len(devs['port_table'])):
                port_poe = devs['port_table'][x]['port_poe']
                if port_poe == True:
                    port_name = devs['port_table'][x]['name']
                    poe_power = round(float(devs['port_table'][x]['poe_power']), 1)
                    poe_voltage = round(float(devs['port_table'][x]['poe_voltage']))
                    self.log(str(switch['name']) + ' Port ' + str(x+1) + ' ' + str(port_name) + ': ' + str(poe_power) + 'W' + ' ' + str(poe_voltage) + 'V')
                    self.set_state(entity + "_port" + str(x+1) + "_power", state = poe_power, attributes = {"friendly_name": port_name, "device_class": "power", "unit_of_measurement": "W", "model": model})
                    self.set_state(entity + "_port" + str(x+1) + "_voltage", state = poe_voltage, attributes = {"friendly_name": port_name, "device_class": "voltage", "unit_of_measurement": "V", "model": model})
                else:
                    self.log(str(switch['name']) + ' Port ' + str(x+1) + ": NOT POE")
