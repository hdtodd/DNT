#! /usr/bin/python3
# mqTest.py
# Use this to confirm that this installation is receiving
#   rtl_433 JSON packets published by the monitoring
#   system's rtl_433/mqtt broker service

import random
import json
import time

from paho.mqtt import client as mqtt_client

## *** BEGIN MODIFY LOCAL PARAMETERS ***
broker = '<monitorhost>'
port = 1883
topic = "rtl_433/<monitorhost>/events"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
# if monitoring system mqtt broker is secured, fill these in
username = '<myusername>'
password = '<mypassword>'
## *** END MODIFY LOCAL PARAMETERS ***

thresh = 2.0
lastEntry = {
    "time":0.0,
    "model":"",
    "id":0
    }


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
#    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
#        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        y = json.loads(msg.payload.decode())
        if "temperature_C" in y.keys():
            eTime = time.mktime(time.strptime(y["time"], "%Y-%m-%d %H:%M:%S"))
            if eTime>lastEntry["time"]+thresh or y["model"]!=lastEntry["model"] or y["id"]!=lastEntry["id"]:
                print(y["time"], " ", y["model"], y["id"],"\t", round(float(y["temperature_C"])*9.0/5.0+32.0,1), "°F")
                lastEntry["time"] = eTime
                lastEntry["model"] = y["model"]
                lastEntry["id"] = y["id"]
        else:
            print("--- NOT A THERMOMETER ---")
            print(y)
            print("-------------------------")
                  
    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
