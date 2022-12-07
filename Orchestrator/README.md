# Orchestrator

This module is written in python.
The orchestrator listens for sensor clients when they publish data, and take some decision:
in this case it monitors the light intensity and decide to turn on or off lights by
publishing on an other topic.