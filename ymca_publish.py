
import argparse
import json
import os
import paho.mqtt.publish as publish

from ymca_status import get_status

MQTT_HOST = os.environ.get("MQTT_HOST", "homeassistant.local")
MQTT_PORT =  int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = "ymca/pool/status"
MQTT_DISCOVERY_TOPIC = "homeassistant/device/ymca_pool/config"


def read_status():
    """Read the status JSON"""
    with open("status.json", encoding="utf-8", mode="r") as f:
        data = json.load(f)
        return data


def publish_status():
    """Publish the status to HA using MQTT"""
    status = read_status()

    publish.single(
        MQTT_TOPIC,
        payload=json.dumps(status),
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        retain=True,
        auth={"username": os.environ.get("MQTT_USER"),
            "password": os.environ.get("MQTT_PASS")
            },
    )

def publish_discovery():
    """Publish the device discovery info to HA using MQTT"""
    payload = {
        # device info
        "dev": {
            "ids": ["ymca_pool"],
            "name": "YMCA Pool",
            "mf": "Custom",
            "mdl": "Pool Schedule",
        },
        # origin info
        "o": {
            "name": "ymca_pool_publisher",
            "sw": "1.0.0",
            "url": "https://github.com/havok2063/ymca_pool",
        },
        # topic to listen for updates
        "state_topic": MQTT_TOPIC,
        # components info - defines HA entities
        "cmps": {
            "current_event": {
                "p": "sensor",
                "name": "Current Event",
                "value_template": "{{ value_json.now }}",
                "unique_id": "ymca_pool_current_event",
                "icon": "mdi:pool",
            },
            "next_event": {
                "p": "sensor",
                "name": "Next Event",
                "value_template": "{{ value_json.next }}",
                "unique_id": "ymca_pool_next_event",
                "icon": "mdi:clock-outline",
            },
            "next_time": {
                "p": "sensor",
                "name": "Next Event Time",
                "value_template": "{{ value_json.next_time }}",
                "unique_id": "ymca_pool_next_time",
                "device_class": "timestamp",
                "icon": "mdi:calendar-clock",
            },
            "current_time": {
                "p": "sensor",
                "name": "Status Generated Time",
                "value_template": "{{ value_json.current_time }}",
                "unique_id": "ymca_pool_current_time",
                "device_class": "timestamp",
                "entity_category": "diagnostic",
            },
            "lanes_free": {
                "p": "sensor",
                "name": "Lanes Free",
                "value_template": "{{ value_json.lanes_free }}",
                "unique_id": "ymca_pool_lanes_free",
                "unit_of_measurement": "lanes",
                "state_class": "measurement",
                "icon": "mdi:counter",
            },
            "lanes_used": {
                "p": "sensor",
                "name": "Lanes Used",
                "value_template": "{{ value_json.lanes_used }}",
                "unique_id": "ymca_pool_lanes_used",
                "unit_of_measurement": "lanes",
                "state_class": "measurement",
                "icon": "mdi:counter",
            },
            "lane_band": {
                "p": "sensor",
                "name": "Lane Band",
                "value_template": "{% set lanes = value_json.lanes_free | int(0) %}{% if lanes <= 1 %}low{% elif lanes <= 3 %}medium{% else %}high{% endif %}",
                "unique_id": "ymca_pool_lane_band",
                "icon": "mdi:traffic-light",
            },
            "active_events": {
                "p": "sensor",
                "name": "Active Events",
                "value_template": "{{ value_json.active_events | join(', ') }}",
                "unique_id": "ymca_pool_active_events",
                "icon": "mdi:format-list-bulleted",
            },
            "lap_available": {
                "p": "binary_sensor",
                "name": "Lap Lanes Available",
                "value_template": "{{ 'ON' if (value_json.lanes_free | int(0)) > 0 else 'OFF' }}",
                "unique_id": "ymca_pool_lap_available",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "occupancy",
                "icon": "mdi:pool",
            },
        },
    }

    publish.single(
        MQTT_DISCOVERY_TOPIC,
        payload=json.dumps(payload),
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        retain=True,
        auth={
            "username": os.environ.get("MQTT_USER"),
            "password": os.environ.get("MQTT_PASS"),
        },
    )

def main() -> None:
    "main"
    parser = argparse.ArgumentParser(description="Publish the YMCA status to HA.")
    parser.add_argument("-s", "--status", action='store_true', default=False, help="Publish the status")
    parser.add_argument("-d", "--device", action='store_true', default=False, help="Publish the device info")
    args = parser.parse_args()

    if args.status:
        # get the updated status
        get_status()
        # publish it
        publish_status()
    elif args.device:
        # publish the discovery device info
        publish_discovery()



if __name__ == "__main__":
    main()
