# ymca_pool
YMCA pool schedule retriever

This script pulls the YMCA lap pool schedule for the current week, for the Orokawa Branch at the Y in Maryland.  It writes the content
as a JSON file.  The index.html page is a simple website to display the schedule as a weekly calendar of pool events, with lap lane info.

Run `python ymca_fetch.py` to get the schedule and write to a `lap_pool_week.json` file.

Run `python -m http.server [port]` to start a local webserver, which loads the `index.html` page.

Run `python ymca_status.py` to generate a new `status.json` file.  This file contains current pool event info extracted into a single json, for publishing to Home Assistant.

Run `python ymca_publish.py --status` to publish to new status to your Home Assistant using [MQTT](https://www.home-assistant.io/integrations/mqtt). Run this periodically.

Run `python ymca_publish.py --device` to publish the [Device Discovery](https://www.home-assistant.io/integrations/mqtt/#device-discovery-payload) info to Home Assistant.  Run this once one first setup.


**Note**: this entire codebase was vibe coded with gpt-5.3-codex.
