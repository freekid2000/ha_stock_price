from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.const import CONF_NAME
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging
import requests
import re

CONF_TRACKING_NUMBER = 'tracking_number'
DEFAULT_NAME = 'stock_pirce_check'
ICON = 'mdi:cash-usd-outline'
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_TRACKING_NUMBER): dict,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})
_Log=logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    tracking_number = config.get(CONF_TRACKING_NUMBER)
    name = config.get(CONF_NAME)
    if tracking_number == None:
        _Log.error('缺少股票代码(tracking_number)!')
    dev = []

    for key, value in tracking_number.items():
        dev.append(StockPriceSensor(hass, name+'_'+value, key, value))
    add_devices(dev, True)

class StockPriceSensor(Entity):
    def __init__(self, hass, sensor_name,  friendly_name, tracking_number):
        """Initialize the sensor."""
        self._name = friendly_name
        self.entity_id = generate_entity_id('sensor.{}', sensor_name, hass=hass)
        self.tracking_number = tracking_number
        self.attributes = {
            '今日开盘价': 0.00,
            '昨日收盘价': 0.00,
            '今日最高价': 0.00,
            '今日最低价': 0.00
        }
        self._state = None
        self.cashtag = '¥'

    @property
    def should_poll(self):
        """No polling needed for a demo sensor."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self.cashtag

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self.attributes

    def get_price(self):
        str_sina_jsres = requests.get("http://hq.sinajs.cn/list="+self.tracking_number).text

        matchObj = re.search( r'var hq_str_(.*?)="(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),.*,([^,]+),[^,]+.?"', str_sina_jsres, re.I|re.M)
        _Log.info("Match %s", str(self.tracking_number+", found: "+matchObj.group(1)))
        if matchObj:
            matchObjSH = re.match(r'sh\d{6}', matchObj.group(1), re.I)
            matchObjSZ = re.match(r'sz\d{6}', matchObj.group(1), re.I)
            matchObjHK = re.match(r'hk\d{5}', matchObj.group(1), re.I)
            matchObjUS = re.match(r'gb_.+', matchObj.group(1), re.I)
            if matchObjSH or matchObjSZ:
                # str_stockinfo = str(matchObj.group(5))[0:6] + "|开" + str(matchObj.group(3))[0:6] + "|高" + str(matchObj.group(6))[0:6] + "|低" + str(matchObj.group(7))[0:6]
                str_stockinfo = matchObj.group(5)
                self.cashtag = 'CN¥'
                self.attributes = {
                    '今日开盘价': matchObj.group(3),
                    '昨日收盘价': matchObj.group(4),
                    '今日最高价': matchObj.group(6),
                    '今日最低价':matchObj.group(7)
                }
            elif matchObjHK:
                str_stockinfo = matchObj.group(8)
                self.cashtag = 'HK$'
                self.attributes = {
                    '今日开盘价': matchObj.group(4),
                    '昨日收盘价': matchObj.group(5),
                    '今日最高价': matchObj.group(6),
                    '今日最低价':matchObj.group(7)
                }
            elif matchObjUS:
                str_stockinfo = matchObj.group(3)
                self.cashtag = 'US$'
                self.attributes = {
                    '今日开盘价': matchObj.group(7),
                    '昨日收盘价': matchObj.group(10),
                    '今日最高价': matchObj.group(8),
                    '今日最低价':matchObj.group(9)
                }
            else:
                str_stockinfo = "No match."

        else:
            str_stockinfo = "No response!"

        return str_stockinfo


    def update(self):
        """Get the latest entry from a file and updates the state."""
        _Log.info("update: %s", self.tracking_number)
        self._state = self.get_price()
