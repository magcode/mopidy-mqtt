# future imports
from __future__ import absolute_import
from __future__ import unicode_literals

# stdlib imports
import logging
import time

from mopidy import core

import paho.mqtt.client as mqtt

# third-party imports
import pykka

logger = logging.getLogger(__name__)

class MQTTFrontend(pykka.ThreadingActor, core.CoreListener):

    def on_stop(self):
        logger.info("mopidy_mqtt shutting down ... ")
        self.mqttClient.disconnect()
        
    def __init__(self, config, core):
        logger.info("mopidy_mqtt initializing ... ")
        self.core = core
        self.mqttClient = mqtt.Client(client_id="mopidy-" + str(int(round(time.time() * 1000))), clean_session=True)
        self.mqttClient.on_message = self.mqtt_on_message
        self.mqttClient.on_connect = self.mqtt_on_connect     
        
        self.config = config['mqtthook']
        host = self.config['mqtthost']
        port = self.config['mqttport']
        self.topic = self.config['topic']
        if self.config['username'] and self.config['password']:
            self.mqttClient.username_pw_set(self.config['username'], password=self.config['password'])
        self.mqttClient.connect_async(host, port, 60)        
        
        self.mqttClient.loop_start()
        super(MQTTFrontend, self).__init__()
        self.MQTTHook = MQTTHook(self, core, config, self.mqttClient)
        
    def mqtt_on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with result code %s" % rc)
        
        rc = self.mqttClient.subscribe(self.topic + "/play")
        if rc[0] != mqtt.MQTT_ERR_SUCCESS:            
            logger.warn("Error during subscribe: " + str(rc[0]))
        else:
            logger.info("Subscribed to " + self.topic + "/play")
        self.mqttClient.subscribe(self.topic + "/control")
        logger.info("sub:" + self.topic + "/control")
        self.mqttClient.subscribe(self.topic + "/volume")
        logger.info("sub:" + self.topic + "/volume")

    def mqtt_on_message(self, mqttc, obj, msg):
        logger.info("received a message on " + msg.topic+" with payload "+str(msg.payload))
        topPlay = self.topic + "/play"
        topControl = self.topic + "/control"
        topVolume = self.topic + "/volume"

        if msg.topic == topPlay:
            self.core.tracklist.clear()
            self.core.tracklist.add(None, None, str(msg.payload), None)
            self.core.playback.play()
            
        if msg.topic == topControl:
            if msg.payload == "stop":
                self.core.playback.stop()
            elif msg.payload == "pause":
                self.core.playback.pause()
            elif msg.payload == "play":
                self.core.playback.play()
            elif msg.payload == "resume":
                self.core.playback.resume()
            elif msg.payload == "next":
                self.core.playback.next()
            elif msg.payload == "previous":
                self.core.playback.previous()

        if msg.topic == topVolume:
            try:
                volume=int(msg.payload)
                self.core.mixer.set_volume(volume)
            except ValueError:
                logger.warn("invalid payload for volume: " + msg.payload)

    def stream_title_changed(self, title):
        self.MQTTHook.send_title(title)

    def playback_state_changed(self, old_state, new_state):
        self.MQTTHook.send_playback_state(new_state)
        if (new_state == "stopped"):
            self.MQTTHook.send_title("stopped")
        
    def track_playback_started(self, tl_track):
        track = tl_track.track
        artists = ', '.join(sorted([a.name for a in track.artists]))
        self.MQTTHook.send_title(artists + ":" + track.name)
        try:
            album = track.album
            albumImage = next(iter(album.images))
            self.MQTTHook.send_image(albumImage)
        except:
            logger.debug("no image")
        
class MQTTHook():
    def __init__(self, frontend, core, config, client):
        self.config = config['mqtthook']        
        self.mqttclient = client
        
    def send_playback_state(self, state):
        try:
            topic = self.config['topic'] + "/state"
            rc = self.mqttclient.publish(topic, state)
            if rc[0] == mqtt.MQTT_ERR_NO_CONN:            
                logger.warn("Error during publish: MQTT_ERR_NO_CONN")
            else:
                logger.info("Sent " + state + " to " + topic)
        except Exception as e:
            logger.warning('Unable to send', exc_info=True)
            
    def send_title(self, title):
        try:
            topic = self.config['topic'] + "/nowplaying"
            rc = self.mqttclient.publish(topic, title)
            if rc[0] == mqtt.MQTT_ERR_NO_CONN:            
                logger.warn("Error during publish: MQTT_ERR_NO_CONN")
            else:
                logger.info("Sent " + title + " to " + topic)
        except Exception as e:
            logger.warning('Unable to send', exc_info=True)

    def send_image(self, image):
        try:
            topic = self.config['topic'] + "/image"
            rc = self.mqttclient.publish(topic, image)
            if rc[0] == mqtt.MQTT_ERR_NO_CONN:            
                logger.warn("Error during publish: MQTT_ERR_NO_CONN")
            else:
                logger.info("Sent " + image + " to " + topic)
        except Exception as e:
            logger.warning('Unable to send', exc_info=True)
