# future imports
from __future__ import absolute_import
from __future__ import unicode_literals

# stdlib imports
import logging
import time
import requests
from PIL import Image
import base64
from io import BytesIO

from mopidy import core

import paho.mqtt.client as mqtt

# third-party imports
import pykka

logger = logging.getLogger(__name__)

class MQTTFrontend(pykka.ThreadingActor, core.CoreListener):

    def __init__(self, config, core):
        logger.info("Initializing ... ")
        self.core = core
        self.mqttClient = mqtt.Client(client_id="mopidy-" + str(int(round(time.time() * 1000))), clean_session=True)
        self.mqttClient.on_message = self.mqtt_on_message
        self.mqttClient.on_connect = self.mqtt_on_connect
        
        self.config = config['mqtthook']
        host = self.config['mqtthost']
        port = self.config['mqttport']
        tls = self.config['tls']
        self.stoppedImage = self.config['stoppedimage']
        self.defaultImage = self.config['defaultimage']
        self.publishBase64Image = self.config['publishbase64image']
        self.topic = self.config['topic']
        if tls:
            self.mqttClient.tls_set()
        if self.config['username'] and self.config['password']:
            self.mqttClient.username_pw_set(self.config['username'], password=self.config['password'])
        self.mqttClient.connect_async(host, port, 60)        
        
        self.mqttClient.loop_start()
        super(MQTTFrontend, self).__init__()
        self.MQTTHook = MQTTHook(self, core, config, self.mqttClient)
        
    def mqtt_on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with result code %s" % rc)
        for sub in ["/play","/control","/volume","/info","/search"]:
            rc = self.mqttClient.subscribe(self.topic+sub)
            if rc[0] != mqtt.MQTT_ERR_SUCCESS:
                logger.warn("Error during subscribe: " + str(rc[0]))
            else:              
                logger.info("Subscribed to " + self.topic + sub)

    def mqtt_on_message(self, mqttc, obj, msg):
        payload = msg.payload.decode()
        logger.info("received a message on " + msg.topic+" with payload " + payload)
        topPlay = self.topic + "/play"
        topControl = self.topic + "/control"
        topVolume = self.topic + "/volume"
        topInfo = self.topic + "/info"
        topSearch = self.topic + "/search"

        if msg.topic == topPlay:
            self.core.tracklist.clear()
            self.core.tracklist.add(uris=[payload])
            self.core.playback.play()
        elif msg.topic == topControl:
            if payload == "stop":
                self.core.playback.stop()
            elif payload == "pause":
                self.core.playback.pause()
            elif payload == "play":
                self.core.playback.play()
            elif payload == "resume":
                self.core.playback.resume()
            elif payload == "next":
                self.core.playback.next()
            elif payload == "previous":
                self.core.playback.previous()
            elif payload == "volplus":
                vol=self.core.mixer.get_volume().get()+10
                if (vol>100):
                    vol=100
                self.core.mixer.set_volume(vol)
            elif payload == "volminus":
                vol=self.core.mixer.get_volume().get()-10
                if (vol<0):
                    vol=0
                self.core.mixer.set_volume(vol)

        elif msg.topic == topVolume:
            try:
                volume=int(msg.payload)
                self.core.mixer.set_volume(volume)
            except ValueError:
                logger.warn("invalid payload for volume: " + msg.payload)
        elif msg.topic == topInfo:
            if msg.payload == "volume":
                self.MQTTHook.publish("/info","volume;"+str(self.core.mixer.get_volume().get()))
            elif msg.payload == "list":
                plist=self.core.playlists.as_list()
                for a in plist.get():
                    self.MQTTHook.publish("/lists","%s;%s"%(a.name,a.uri) )
        elif msg.topic == topSearch:
            search=msg.payload.replace("de ","")
            res=self.core.library.search({'any': [search]},uris=['local:']).get()
            found=(len(res[0].tracks))
            logger.info("Adding %d tunes from %s"%(found,search))
            
            if (found>0):
                self.core.tracklist.clear()
                self.core.tracklist.add(tracks=res[0].tracks)
                self.MQTTHook.publish("/state","Adding %d tunes from %s"%(found,search))
                self.core.mixer.set_volume(7)
                self.core.playback.play()


    def on_stop(self):
        logger.info("mopidy_mqtt shutting down ... ")
        self.mqttClient.disconnect()
        
    def stream_title_changed(self, title):
        logger.info("before" + title)
        titleStripped = title.rstrip('.mp3')
        logger.info("after" + titleStripped)
        self.MQTTHook.publish("/nowplaying", titleStripped)

    def playback_state_changed(self, old_state, new_state):
        self.MQTTHook.publish("/state", new_state)
        if (new_state == "stopped"):
            self.MQTTHook.publish("/nowplaying", "stopped")
            self.MQTTHook.publish("/image", self.stoppedImage)
            
        
    def track_playback_started(self, tl_track):
        track = tl_track.track
        artists="unknown"
        if (len(track.artists)>0):
            artists = ', '.join(sorted([a.name for a in track.artists]))
        if (track.name is None):
            tn="stream"
        else:
            tn=track.name
        tn = tn.rstrip('.mp3')
        self.MQTTHook.publish("/nowplaying", artists + ":" + tn)
        imageUri=self.core.library.get_images([track.uri]).get()[track.uri]
        if (imageUri):
          self.MQTTHook.publish("/image", imageUri[0].uri)
          if self.publishBase64Image:
            self.base64_image_publish(imageUri[0].uri)
        else:
          self.MQTTHook.publish("/image", self.defaultImage)

    def base64_image_publish(self, imageUri):
        defaultHeaders = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}
        response = requests.get(imageUri,headers=defaultHeaders)
        img = Image.open(BytesIO(response.content))
        new_image = img.resize((8, 8))
        temp = BytesIO()
        new_image.save(temp,format="JPEG")
        encoded_image = base64.b64encode(temp.getvalue())
        self.MQTTHook.publish("/imageBase64", encoded_image.decode('ascii'))
        
class MQTTHook():
    def __init__(self, frontend, core, config, client):
        self.config = config['mqtthook']        
        self.mqttclient = client
       
    def publish(self, topic, state):
        full_topic = self.config['topic'] + topic
        try:
            rc = self.mqttclient.publish(full_topic, state)
            if rc[0] == mqtt.MQTT_ERR_NO_CONN:            
                logger.warn("Error during publish: MQTT_ERR_NO_CONN")
            else:
                logger.info("Sent " + state + " to " + full_topic)
        except Exception as e:
            logger.error('Unable to send', exc_info=True)
