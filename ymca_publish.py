
import argparse
import json
import os
import paho.mqtt.publish as publish

from ymca_status import get_status

MQTT_HOST = os.environ.get("MQTT_HOST", "homeassistant.local")
MQTT_PORT =  int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = "ymca/pool/status"


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
    base = "homeassistant/sensor/ymca"

    device = {
        "identifiers": ["ymca_pool"],
        "name": "YMCA Pool",
        "manufacturer": "Custom",
        "model": "Pool Schedule",
    }

    configs = [
        {
            "topic": f"{base}_now/config",
            "payload": {
                "name": "YMCA Now",
                "state_topic": MQTT_TOPIC,
                "value_template": "{{ value_json.now }}",
                "unique_id": "ymca_now",
                "device": device,
            },
        },
        {
            "topic": f"{base}_lanes/config",
            "payload": {
                "name": "YMCA Lanes Free",
                "state_topic": MQTT_TOPIC,
                "value_template": "{{ value_json.lanes_free }}",
                "unit_of_measurement": "lanes",
                "unique_id": "ymca_lanes",
                "device": device,
            },
        },
        {
            "topic": f"{base}_next/config",
            "payload": {
                "name": "YMCA Next",
                "state_topic": MQTT_TOPIC,
                "value_template": "{{ value_json.next }}",
                "unique_id": "ymca_next",
                "device": device,
            },
        },
    ]

    msgs = [
        {
            "topic": c["topic"],
            "payload": json.dumps(c["payload"]),
            "retain": True,
            "qos": 0,
        }
        for c in configs
    ]

    publish.multiple(
        msgs,
        hostname=MQTT_HOST,
        port=MQTT_PORT,
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
