# MQTT Accessibility Device Lifecycle Handler

This script handles dynamic subscriptions for `accessibility` topics under Zigbee2MQTT. It maintains a cache of device state (online/offline), subscribes to topics for newly online devices, and unsubscribes from topics when devices go offline. It avoids duplicate actions and handles misconfigurations gracefully.

---

## 1. Base Subscription

You start by subscribing to all online/offline status messages for accessibility devices under the Zigbee2MQTT bridge.

**Universal subscription pattern:**

~~~~python
client.subscribe("+/bridge/+/accessibility")
~~~~

This will catch:
- `zigbee2mqtt/bridge/device_friendly_name/accessibility`

---

## 2. On Message: Detect Device Lifecycle Transitions

Use the `topic` to extract:

- `zigbee_base` (e.g., `zigbee2mqtt`)
- `device_id` or `friendly_name`
- `state` = payload (`online` or `offline`)

Then maintain a cache (dict) of current device states:

~~~~python
device_states = {}  # Key: (zigbee_base, device_id) → "online"/"offline"

def handle_accessibility(topic, payload):
    zigbee_base, _, device_id, _ = topic.split("/", 3)
    state = payload.lower()

    key = (zigbee_base, device_id)
    previous = device_states.get(key)

    if state == "offline":
        device_states[key] = "offline"
        if previous == "online":
            topic_to_unsub = f"{zigbee_base}/{device_id}/#"
            client.unsubscribe(topic_to_unsub)

    elif state == "online":
        device_states[key] = "online"
        if previous != "online":
            topic_to_sub = f"{zigbee_base}/{device_id}/#"
            client.subscribe(topic_to_sub)

            # Optional: initial discovery after subscribe
            discovery_topic = f"{zigbee_base}/{device_id}"
            client.publish("discovery/request", discovery_topic)
~~~~

---

## 3. Edge Case Handling

- If the device is **not in the cache** and the state is `"offline"` → add to cache but **do nothing**.
- If the state changes from **offline → online** → `subscribe`
- If the state changes from **online → offline** → `unsubscribe`
- If a device is already online or offline in the cache → **ignore repeat messages**

---

## 4. Device Discovery (Optional Enhancement)

After subscribing to `zigbee_base/device_id/#`, optionally trigger a discovery action (if your system supports it):

~~~~python
discovery_topic = f"{zigbee_base}/{device_id}"
client.publish("discovery/request", discovery_topic)
~~~~

You could also directly inspect retained topics for attributes or states under:

- `zigbee2mqtt/<device>/availability`
- `zigbee2mqtt/<device>/state`
- `zigbee2mqtt/<device>/friendly_name`
- `zigbee2mqtt/<device>/definition`

---

## 5. Summary

- You only subscribe/unsubscribe to dynamic topics like `zigbee2mqtt/<device>/#` if the state changes.
- Cache ensures you don’t re-react to duplicate status updates or bad device configs.
- Edge case: if multiple messages for the same device come in simultaneously, only the **first online** triggers subscription.

This logic gives you full dynamic control of accessibility topic handling based on actual device lifecycles.