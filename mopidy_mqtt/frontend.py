# future imports
from __future__ import absolute_import
from __future__ import unicode_literals

# stdlib imports
import logging

from mopidy import core

import paho.mqtt.client as mqtt

# third-party imports
import pykka

logger = logging.getLogger(__name__)


class MQTTFrontend(pykka.ThreadingActor, core.CoreListener):

    def __init__(self, config, core):
        self.core = core
        self.client = mqtt.Client()
        self.client.on_message = self.mqtt_on_message
        self.config = config['mqtthook']
        host = self.config['mqtthost']
        port = self.config['mqttport']
        topic = self.config['topic']
        self.client.connect(host, port, 60)
        self.client.subscribe(topic + "/play")
        self.client.loop_start()
        super(MQTTFrontend, self).__init__()
        self.MQTTHook = MQTTHook(self, core, config, self.client)
        
    def mqtt_on_message(self, mqttc, obj, msg):
        logger.info("received play message on " + msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        self.core.tracklist.clear()
        self.core.tracklist.add(None, None, str(msg.payload), None)
        self.core.playback.play()
    
    def stream_title_changed(self, title):
        self.MQTTHook.send_title(title)

    def playback_state_changed(self, old_state, new_state):
        self.MQTTHook.send_playback_state(new_state)
        
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
            logger.info('Sending ')
            topic = self.config['topic'] + "/state"
            self.mqttclient.publish(topic, state)
        except Exception as e:
            logger.warning('Unable to send')
        else:
            logger.info('OK ')
            
    def send_title(self, title):
        try:
            logger.info('Sending ')
            topic = self.config['topic'] + "/nowplaying"
            self.mqttclient.publish(topic, title)
        except Exception as e:
            logger.warning('Unable to send')
        else:
            logger.info('OK ')

    def send_image(self, image):
        try:
            logger.info('Sending ')
            topic = self.config['topic'] + "/image"
            self.mqttclient.publish(topic, image)
        except Exception as e:
            logger.warning('Unable to send')
        else:
            logger.info('OK ')