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

## Stop playback
You can stop the playback via MQTT. Send the following:

`mytopic/control -> 'stop'`

## Change volume
You can change the mixer volume from 0 to 100 via MQTT. Send the following:

`mytopic/volume -> '50'`

# Installation

This is an example how to install on a Raspi:

```
cd ~
git clone https://github.com/magcode/mopidy-mqtt.git
cd mopidy-mqtt
sudo python3 setup.py develop
```
Alternatively for a local installation you can change the last line to
```
python3 setup.py install --user
```

Now configure the following file: `/etc/mopidy/mopidy.conf`

```
[mqtthook]
enabled = true
mqtthost = <mqtt host>
mqttport = <mqtt port>
username = <mqtt username> (Optional)
password = <mqtt password> (Optional)
topic = <topic, e.g. home/livingroom/music>
```

Restart Mopidy with `sudo service mopidy restart`

To check Mopidy log run `sudo tail -f /var/log/mopidy/mopidy.log`
