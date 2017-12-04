# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for Sensortag CC2650 'poll' type plugin """

import copy
import datetime
import uuid

import asyncio

from foglamp.plugins.south.common.sensortag_cc2650 import *
from foglamp.common.parser import Parser
from foglamp.services.south import exceptions
from foglamp.common import logger

__author__ = "Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'Python module name of the plugin to load',
         'type': 'string',
         'default': 'cc2650poll'
    },
    'pollInterval': {
        'description': 'The interval between poll calls to the device poll routine expressed in milliseconds.',
        'type': 'integer',
        'default': '500'
    },
    'bluetooth_address': {
        'description': 'Bluetooth MAC address',
        'type': 'string',
        'default': 'B0:91:22:EA:79:04'
    }
}

_LOGGER = logger.setup(__name__, level=20)

sensortag_characteristics = characteristics


def plugin_info():
    """ Returns information about the plugin.

    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'Poll plugin',
        'version': '1.0',
        'mode': 'poll',
        'type': 'device',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.

    Args:
        config: JSON configuration document for the device configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    global sensortag_characteristics

    bluetooth_adr = config['bluetooth_address']['value']
    tag = SensorTagCC2650(bluetooth_adr)

    # The GATT table can change for different firmware revisions, so it is important to do a proper characteristic
    # discovery rather than hard-coding the attribute handles.
    for char in sensortag_characteristics.keys():
        for type in ['data', 'configuration', 'period']:
            handle = tag.get_char_handle(sensortag_characteristics[char][type]['uuid'])
            sensortag_characteristics[char][type]['handle'] = handle

    # print(json.dumps(sensortag_characteristics))

    data = copy.deepcopy(config)
    data['characteristics'] = sensortag_characteristics
    data['bluetooth_adr'] = bluetooth_adr

    _LOGGER.info('SensorTagCC2650 {} Polling initialized'.format(bluetooth_adr))

    return data


def plugin_poll(handle):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.

    Available for poll mode only.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        DataRetrievalError
    """

    time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
    data = {
        'asset': 'TI sensortag',
        'timestamp': time_stamp,
        'key': str(uuid.uuid4()),
        'readings': {}
    }

    try:
        bluetooth_adr = handle['bluetooth_adr']
        object_temp_celsius = None
        ambient_temp_celsius = None
        lux_luminance = None
        rel_humidity = None
        rel_temperature = None
        bar_pressure = None
        movement = None

        # print(('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))  )
        tag = SensorTagCC2650(bluetooth_adr)  # pass the Bluetooth Address

        # Enable sensors
        tag.char_write_cmd(handle['characteristics']['temperature']['configuration']['handle'], char_enable)
        tag.char_write_cmd(handle['characteristics']['luminance']['configuration']['handle'], char_enable)
        tag.char_write_cmd(handle['characteristics']['humidity']['configuration']['handle'], char_enable)
        tag.char_write_cmd(handle['characteristics']['pressure']['configuration']['handle'], char_enable)
        tag.char_write_cmd(handle['characteristics']['movement']['configuration']['handle'], movement_enable)

        # Get temperature
        count = 0
        while count < SensorTagCC2650.reading_iterations:
            object_temp_celsius, ambient_temp_celsius = tag.hexTemp2C(tag.char_read_hnd(
                handle['characteristics']['temperature']['data']['handle'], "temperature"))
            time.sleep(0.5)  # wait for a while
            count = count + 1

        # Get luminance
        lux_luminance = tag.hexLum2Lux(tag.char_read_hnd(
            handle['characteristics']['luminance']['data']['handle'], "luminance"))

        # Get humidity
        rel_humidity, rel_temperature = tag.hexHum2RelHum(tag.char_read_hnd(
            handle['characteristics']['humidity']['data']['handle'], "humidity"))

        # Get pressure
        bar_pressure = tag.hexPress2Press(tag.char_read_hnd(
            handle['characteristics']['pressure']['data']['handle'], "pressure"))

        # Get movement
        gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z, mag_x, mag_y, mag_z, acc_range = tag.hexMovement2Mov(tag.char_read_hnd(
            handle['characteristics']['movement']['data']['handle'], "movement"))
        movement = {
            'gyro': {
                'x': gyro_x,
                'y': gyro_y,
                'z': gyro_z,
            },
            'acc': {
                'x': acc_x,
                'y': acc_y,
                'z': acc_z,
            },
            'mag': {
                'x': mag_x,
                'y': mag_y,
                'z': mag_z,
            },
            'acc_range': acc_range
        }

        # Disable sensors
        tag.char_write_cmd(handle['characteristics']['temperature']['configuration']['handle'], char_disable)
        tag.char_write_cmd(handle['characteristics']['luminance']['configuration']['handle'], char_disable)
        tag.char_write_cmd(handle['characteristics']['humidity']['configuration']['handle'], char_disable)
        tag.char_write_cmd(handle['characteristics']['pressure']['configuration']['handle'], char_disable)
        tag.char_write_cmd(handle['characteristics']['movement']['configuration']['handle'], movement_disable)

        # "values" (and not "readings") denotes that this reading needs to be further broken down to components.
        data['readings'] = {
            'temperature': {
                "object": object_temp_celsius,
                'ambient': ambient_temp_celsius
            },
            'luxometer': {"lux": lux_luminance},
            'humidity': {
                "humidity": rel_humidity,
                "temperature": rel_temperature
            },
            'pressure': {"pressure": bar_pressure},
            'gyroscope': {
                "x": gyro_x,
                "y": gyro_y,
                "z": gyro_z
            },
            'accelerometer': {
                "x": acc_x,
                "y": acc_y,
                "z": acc_z
            },
            'magnetomer': {
                "x": mag_x,
                "y": mag_y,
                "z": mag_z
            }
        }
        for reading_key in data['readings']:
            asyncio.ensure_future(
                handle['ingest'].add_readings(asset=data['asset'] + '/' + reading_key,
                                    timestamp=data['timestamp'],
                                    key=str(uuid.uuid4()),
                                    readings=data['readings'][reading_key]))
    except Exception as ex:
        _LOGGER.exception("SensorTagCC2650 {} exception: {}".format(bluetooth_adr, str(ex)))
        raise exceptions.DataRetrievalError(ex)

    # _LOGGER.info("SensorTagCC2650 {} reading: {}".format(bluetooth_adr, json.dumps(data)))
    return data


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin, it should be called when the configuration of the plugin is changed during the
        operation of the device service.
        The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """

    new_handle = {}

    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    bluetooth_adr = handle['bluetooth_adr']
    _LOGGER.info('SensorTagCC2650 {} Polling shutdown'.format(bluetooth_adr))
