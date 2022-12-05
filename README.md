# MY SmartHome
This is my own smart home project

It is not intended to be a code for generic use, but a specific a design for a specific domain ence my personal house.
My pourpose is to build from scratch my own smart home system able to integrate with other open source systems like [Home Assistant](https://www.home-assistant.io/).

The main core is build on an old Android TV box ARM based [BQueel M9C PRO](https://www.bqeel.net/products/android-tv-box.html). It was definitely not a good smart TV box -.-' ... so I have left it soon and I have forgotten it.
![BQueel M9C PRO](https://www.cdiscount.com/pdt2/6/1/6/1/700x700/auc0643845678616/rw/bqeel-m9c-pro-android-tv-box-amlogic-s905x-quad-co.jpg)

I have thought about it again when I discovered [Armbian OS](https://www.armbian.com/). So I decided to build the core (or at least part of it) on that HW with that OS. :)

Every SW module is conteinerized on [Docker](https://www.docker.com/)
So, the core project is composed by four SW modules:
    -   MQTT Broker: I have choosed RabbitMQ so I already had experience on that
    -   Database Postgresql: open source and highly supported
    -   Consumer: a MQTT python3.10 client which collect data coming from other MQTT client with sensors onboard and stores them into DB
    -   Manager:  MQTT python3.10 client which temporizes the data published by other MQTT client with sensors onboard
    -   Orchestrator: MQTT python3.10 client which listens on every published data from client sensor and decide to make some action (like publish on an other topic to turn on or off lights)

Every single folder contains more specific description of single module.

This is open source project, you are free to contribute.
if you want to write me this is my email [andrealisi88@gmail.com]