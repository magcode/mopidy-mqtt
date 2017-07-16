# Features

This Mopidy Frontend Extension allows you to control Mopidy with MQTT and retrieve some information from Mopidy via MQTT.
The implementation is very basic. Open for any kind of pull requests.

## Status update

Mopidy sends an update as soon the playback state changes:

`mytopic/state -> 'paused'`

When a new title or stream is started Mopidy sends this via `nowplaying`

`mytopic/nowplaying -> 'myradio'`

## Play a song or stream
You can start playback of a song or stream via MQTT. Send the following:

`mytopic/play -> 'tunein:station:s48720'`


# Installation

This is an example how to install on a Raspi:

```
cd ~
git clone https://github.com/magcode/mopidy-mqtt.git
cd mopidy-mqtt
sudo python setup.py develop
```

Now configure the following file: `/etc/mopidy/mopidy.conf`

```
[mqtthook]
enabled = true
mqtthost = <mqtt host>
mqttport = <mqtt port>
topic = <topic, e.g. home/livingroom/music>
```

Restart Mopidy with `sudo service mopidy restart`

To check Mopidy log run `sudo tail -f /var/log/mopidy/mopidy.log`
