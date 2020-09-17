from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext

__version__ = '0.2.0'
logger = logging.getLogger(__name__)

class Extension(ext.Extension):

    dist_name = 'Mopidy-MQTT'
    ext_name = 'mqtthook'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['tls'] = config.Boolean()
        schema['topic'] = config.String()
        schema['mqtthost'] = config.String()
        schema['mqttport'] = config.Integer()
        schema['username'] = config.String()
        schema['password'] = config.String()
        schema['stoppedimage'] = config.String()
        schema['defaultimage'] = config.String()
        return schema

    def setup(self, registry):
        from .frontend import MQTTFrontend
        registry.add('frontend', MQTTFrontend)
