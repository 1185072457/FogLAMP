# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""Unit test for foglamp.device.http_south"""
import json
import pytest
import asyncio
from unittest import mock
from unittest.mock import patch
from aiohttp.test_utils import make_mocked_request
from aiohttp.streams import StreamReader
from multidict import CIMultiDict

from foglamp.device.http_south_device import HttpSouthIngest
from foglamp.device.ingest import Ingest

__author__ = "Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


loop = asyncio.get_event_loop()


def mock_request(data):
    payload = StreamReader(loop=loop)
    payload.feed_data(data.encode())
    payload.feed_eof()

    protocol = mock.Mock()
    app = mock.Mock()
    headers = CIMultiDict([('CONTENT-TYPE', 'application/json')])
    req = make_mocked_request('POST', '/sensor-reading', headers=headers,
                              protocol=protocol, payload=payload, app=app)
    return req


@pytest.allure.feature("unit")
@pytest.allure.story("device")
class TestHttpSouthDeviceUnit(object):
    """Unit tests for foglamp.device.coap.IngestReadings
    """

    @pytest.mark.asyncio
    async def test_post_sensor_reading_ok(self):
        data =  """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor1",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": {
                "velocity": "500",
                "temperature": {
                    "value": "32",
                    "unit": "kelvin"
                }
            }
        }"""
        with patch.object(Ingest, 'add_readings', return_value=asyncio.ensure_future(asyncio.sleep(0.1))) as mock_method1:
            with patch.object(Ingest, 'is_available', return_value=True) as mock_method2:
                request = mock_request(data)
                r = await HttpSouthIngest.render_post(request)
                retval = json.loads(r.body.decode())
                # Assert the POST request response
                assert 200 == retval['status']
                assert 'success' == retval['result']


    @pytest.mark.asyncio
    async def test_post_sensor_reading_bad_1(self):
        data =  """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor1",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": {
                "velocity": "500",
                "temperature": {
                    "value": "32",
                    "unit": "kelvin"
                }
        }"""
        with patch.object(Ingest, 'add_readings', return_value=asyncio.ensure_future(asyncio.sleep(0.1))) as mock_method1:
            with patch.object(Ingest, 'is_available', return_value=True) as mock_method2:
                request = mock_request(data)
                r = await HttpSouthIngest.render_post(request)
                retval = json.loads(r.body.decode())
                print(retval)
                # Assert the POST request response
                assert 400 == retval['status']
                assert retval['error'].startswith("Expecting ',' delimiter:")


    @pytest.mark.asyncio
    async def test_post_sensor_reading_bad_2(self):
        data =  """{
            "timestamp": "2017-01-02T01:02:03.23232Z-05:00",
            "asset": "sensor2",
            "key": "80a43623-ebe5-40d6-8d80-3f892da9b3b4",
            "readings": "500"
        }"""
        with patch.object(Ingest, 'add_readings', return_value=asyncio.ensure_future(asyncio.sleep(0.1))) as mock_method1:
            with patch.object(Ingest, 'is_available', return_value=True) as mock_method2:
                request = mock_request(data)
                r = await HttpSouthIngest.render_post(request)
                retval = json.loads(r.body.decode())
                print(retval)
                # Assert the POST request response
                assert 400 == retval['status']
                assert "readings must be a dictionary" == retval['error']

