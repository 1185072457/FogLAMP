#!/usr/bin/env python3

# -*- coding: utf-8 -*-

""" This module is for test purpose only!

USE src/python/foglamp/storage/payload_builder.py

This will go away when tests, payload_builder and actually STORAGE layer (FOGL-197) are in place

"""

import json
from collections import OrderedDict

from foglamp.common.storage_client.storage_client import StorageClient, ReadingsStorageClient
from foglamp.common.storage_client.exceptions import *


def insert_data():
    print("StorageClient::insert_data :")
    data = dict()

    data['key'] = 'SENT_test'
    data['history_ts'] = 'now'
    data['value'] = 1

    res = StorageClient().insert_into_tbl("statistics_history", json.dumps(data))
    print(res)


def update_data():
    print("StorageClient::update_data :")

    condition = dict()

    condition['column'] = 'key'
    condition['condition'] = '='
    condition['value'] = 'SENT_test'

    values = dict()
    values['value'] = 444

    data = dict()
    data['condition'] = condition
    data['values'] = values

    res = StorageClient().update_tbl("statistics_history", json.dumps(data))
    print(res)


def delete_tbl_data():
    print("StorageClient::delete_tbl_data :")

    # payload as per doc,
    # see: Plugin Common Delete
    del_cond = dict()
    del_cond['column'] = 'id'
    del_cond['condition'] = '='
    del_cond['value'] = '13081'

    # join these AND/ OR conditions
    del_cond_2 = dict()
    del_cond_2['column'] = 'key'
    del_cond_2['condition'] = '='
    del_cond_2['value'] = 'SENT_test'

    # same as where
    cond = dict()
    cond['where'] = del_cond

    ''' DELETE FROM statistics_history WHERE key = 'SENT_test' AND id='13084' '''
    cond['and'] = del_cond_2

    ''' DELETE FROM statistics_history WHERE key = 'SENT_test' OR id='13084' '''
    cond['or'] = del_cond_2

    res = StorageClient().delete_from_tbl("statistics_history", json.dumps(cond))
    print(res)

    ''' DELETE FROM statistics_history '''
    # res = StorageClient().delete_from_tbl("statistics_history")
    # print(res)


def query_table():
    print("StorageClient::query_table :")

    with StorageClient() as store:
        # commented code
        '''
        query = dict()
        query['key'] = 'COAP_CONF'

        # ASK about approach
        query['blah'] = 'SENSORS'
        query_params = '?'
        for k, v in query.items():
            if not query_params == "?":
                query_params += "&"
            query_params += '{}={}'.format(k, v)
        print("CHECK:", query_params)
        '''

        ''' SELECT * FROM configuration WHERE key='COAP_CONF' '''
        # TODO: check &limit=1 (and offset, order_by) will work here?
        q = 'key=COAP_CONF'
        res = store.query_tbl('configuration', q)
        print(res)

        ''' SELECT * FROM statistics '''
        res = store.query_tbl('statistics')
        print(res)


def query_table_with_payload():
    print("StorageClient::query_table_with_payload :")

    # WHERE key = 'SENT_test'"

    where = OrderedDict()
    where['column'] = 'key'
    where['condition'] = '='
    where['value'] = 'SENT_test'

    # verify AND / OR?
    where_2 = OrderedDict()
    where_2['column'] = 'value'
    where_2['condition'] = '>'
    where_2['value'] = '444'

    aggregate = OrderedDict()
    aggregate['operation'] = 'min'
    aggregate['column'] = 'value'

    query_payload = OrderedDict()
    query_payload['where'] = where_2
    query_payload['and'] = where_2
    # query_payload['or'] = where_2
    # query_payload['aggregate'] = aggregate

    # query_payload['limit'] = 2
    # query_payload['skip'] = 1

    # check ?
    order_by = ""

    payload = json.dumps(query_payload)
    print(payload)

    with StorageClient() as store:
        res = store.query_tbl_with_payload('statistics_history', payload)
    print(res)


def append_readings():
    print("ReadingsStorageClient::append_readings :")
    import uuid
    import random
    readings = []

    def map_reading(asset_code, reading, read_key=None, user_ts=None):
        read = dict()
        read['asset_code'] = asset_code
        print(read_key)
        read['read_key'] = read_key
        read['reading'] = dict()
        read['reading']['rate'] = reading
        read['user_ts'] = "2017-09-21 15:00:09.025655"
        # ingest 2017-01-02T01:02:03.23232Z-05:00
        # asset, key, reading, timestamp
        # storage 2017-09-21 15:00:09.025655
        # asset_code, read_key, reading, user_ts
        return read
    x = str(uuid.uuid4())
    # to use duplicate read_key uuid (ON CONFLICT DO NOTHING)
    for _ in range(1, 2):
        readings.append(map_reading('MyAsset', random.uniform(1.0, 100.1), read_key=str(uuid.uuid4())))

    payload = dict()
    payload['readings'] = readings

    print(json.dumps(payload))

    res = ReadingsStorageClient().append(json.dumps(payload))
    print(res)


def fetch_readings():
    print("ReadingsStorageClient::fetch_readings :")
    # tested,
    # works fine if records are less then count
    # also works fine if reading_id does not exist, {'rows': [], 'count': 0}
    res = ReadingsStorageClient().fetch(reading_id=1, count=2)
    print(res)


def purge_readings():
    print("ReadingsStorageClient::purge_readings :")

    res = ReadingsStorageClient().purge('24', '100071')

    # try many (type checking)
    res = ReadingsStorageClient().purge(24, '100071')

    # res = ReadingsStorageClient().purge(24, '100071', 'puRge')

    res = ReadingsStorageClient().purge(age=24, sent_id=100071, flag='RETAIN')

    try:
        # res = ReadingsStorageClient().purge('b', '100071', 'RETAIN')

        # res = ReadingsStorageClient().purge('1', 'v', 'RETAIN')

        res = ReadingsStorageClient().purge(24, '100071', 'xRETAIN')
    except ValueError:
        print("age or reading is not an integer value :/")
    except InvalidReadingsPurgeFlagParameters:
        print("AS expected, InvalidReadingsPurgeFlagParameters")

    print(res)


def query_readings():
    print("ReadingsStorageClient::query_readings :")

    cond1 = OrderedDict()
    cond1['column'] = 'asset_code'
    cond1['condition'] = '='
    cond1['value'] = 'MyAsset'

    query_payload = OrderedDict()
    query_payload['where'] = cond1

    query_payload['limit'] = 2
    query_payload['skip'] = 1

    print("query_readings payload: ", json.dumps(query_payload))

    res = ReadingsStorageClient().query(json.dumps(query_payload))
    print(res)

    # expected response
    '''{'count': 2, 'rows': [
            {'read_key': 'cdbec41e-9c41-4144-8257-e2ab2242dc76', 'user_ts': '2017-09-21 15:00:09.025655+05:30', 'id': 22, 'reading': {'rate': 92.58901867128075}, 'asset_code': 'MyAsset', 'ts': '2017-09-28 20:18:43.809661+05:30'},
            {'read_key': '6ad3cc76-e859-4c78-8031-91fccbb1a5a9', 'user_ts': '2017-09-21 15:00:09.025655+05:30', 'id': 23, 'reading': {'rate': 24.350853712845392}, 'asset_code': 'MyAsset', 'ts': '2017-09-28 20:19:16.739619+05:30'}
            ]
    }'''


try:
    # TODO: Move to tests :]

    ping_response = StorageClient().check_service_availibility()
    print("check_service_availibility res: ", ping_response)

    """ {'uptime': 1077, 'name': 'storage', 
        'statistics': {'commonInsert': 8, 'commonUpdate': 8, 'commonSimpleQuery': 16, 'commonDelete': 8, 'commonQuery': 8, 
                    'readingQuery': 8, 'readingPurge': 13, 'readingFetch': 8, 'readingAppend': 8, }
        }

    """

    query_table()

    insert_data()

    update_data()

    delete_tbl_data()

    query_table_with_payload()

    append_readings()
    # what happens on conflict?

    fetch_readings()

    # TODO: Shall these value be picked from purge config and passed to it?
    purge_readings()

    query_readings()

    # TODO: verify 1 error payload

    # shutdown_response = StorageClient().shutdown()
    # print("check_shutdown res: ", shutdown_response)
    """  {'message': 'Shutdown in progress'}
    """

except InvalidServiceInstance as ex:
    print(ex.code, ex.message)
except StorageServiceUnavailable as ex:
    print(ex.code, ex.message)
