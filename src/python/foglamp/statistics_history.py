#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""
The following piece of code takes the information found in the statistics table, and stores it's delta value 
(statistics.value - statistics.prev_val) inside the statistics_history table. To complete this, SQLAlchemy will be 
used to execute SELECT statements against statistics, and INSERT against the statistics_history table.  
"""
import sqlalchemy
import sqlalchemy.dialects
import os
from datetime import datetime
from foglamp import logger

__author__ = "Ori Shadmon"
__copyright__ = "Copyright (c) 2017 OSI Soft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


# Set variables for connecting to database
_CONNECTION_STRING = "postgres://foglamp@/foglamp"
try:
  snap_user_common = os.environ['SNAP_USER_COMMON']
  unix_socket_dir = "{}/tmp/".format(snap_user_common)
  _CONNECTION_STRING = _CONNECTION_STRING + "?host=" + unix_socket_dir
except KeyError:
  pass

_logger = logger.setup(__name__)

# Deceleration of tables in SQLAlchemy format
_STATS_TABLE = sqlalchemy.Table('statistics', sqlalchemy.MetaData(),
                                sqlalchemy.Column('key', sqlalchemy.CHAR(10), primary_key=True),
                                sqlalchemy.Column('description', sqlalchemy.VARCHAR('255'), default=''),
                                sqlalchemy.Column('value', sqlalchemy.BIGINT, default=0),
                                sqlalchemy.Column('previous_value', sqlalchemy.BIGINT, default=0),
                                sqlalchemy.Column('ts', sqlalchemy.TIMESTAMP(6),
                                                  default=sqlalchemy.func.current_timestamp()))

"""Description of each column 
key - Corresponding statistics.key value, so that there is awareness of what the history is of
history_ts - the newest timestamp in statistics for that key 
value - delta value between `value` and `prev_val` of statistics
            The point is to know how many actions happened during the X time
ts - current timestamp 
"""
_STATS_HISTORY_TABLE = sqlalchemy.Table('statistics_history', sqlalchemy.MetaData(),
                                        sqlalchemy.Column('key', sqlalchemy.CHAR(10)),
                                        sqlalchemy.Column('history_ts', sqlalchemy.TIMESTAMP(6),
                                                          default=sqlalchemy.func.current_timestamp()),
                                        sqlalchemy.Column('value', sqlalchemy.BIGINT, default=0),
                                        sqlalchemy.Column('ts', sqlalchemy.TIMESTAMP(6),
                                                          default=sqlalchemy.func.current_timestamp())
                                        )


def list_stats_keys() -> list:
    """
    generate a list of distinct keys from statistics table 
    Returns:
        list of distinct keys
    """
    key_list = []
    stmt = sqlalchemy.select([_STATS_TABLE.c.key.distinct()]).select_from(_STATS_TABLE)
    engine = sqlalchemy.create_engine(_CONNECTION_STRING, pool_size=5, max_overflow=0)
    conn = engine.connect()
    try:
        results = conn.execute(stmt)
    except Exception:
        _logger.exception("Failed to retrieve keys from statistics table")
        raise
    for result in results.fetchall():
        key_list.append(result[0].strip())
    conn.close()
    return key_list


def insert_into_stats_history(key: str, value: int, history_ts: datetime):
    """
    INSERT values in statistics_history
    :arg:
        key (str): corresponding stats_key_value
        value (int): delta between `value` and `prev_val`
        history_ts (datetime): timestamp that row was affected
    """
    stmt = _STATS_HISTORY_TABLE.insert().values(key=key, value=value, history_ts=history_ts)
    engine = sqlalchemy.create_engine(_CONNECTION_STRING, pool_size=5, max_overflow=0)
    conn = engine.connect()
    try:
        conn.execute(stmt)
    except Exception:
        _logger.exception("Failed to insert values into statistics_history table")
        raise
    conn.close()


def update_previous_value(key: str, value: int):
    """
    Update previous_value of column to have the same value as snapshot
    :arg:
        key: Key which previous_value gets update 
        value: value at snapshot
    """
    stmt = _STATS_TABLE.update().values(previous_value=value).where(_STATS_TABLE.c.key == key)
    engine = sqlalchemy.create_engine(_CONNECTION_STRING, pool_size=5, max_overflow=0)
    conn = engine.connect()
    try:
        conn.execute(stmt)
    except Exception:
        _logger.exception("Failed to update previous_value into statistics table")
        raise
    conn.close()


def select_from_statistics(key: str) -> (int, int):
    """
    SELECT data from statistics for the statistics_history table
    :arg:
        key (str): The row name update is executed against (WHERE condition)
    :return:
        The integer value of statistics.value and statistics.previous_value
    """
    stmt = sqlalchemy.select([_STATS_TABLE.c.value, _STATS_TABLE.c.previous_value]).where(_STATS_TABLE.c.key == key)
    engine = sqlalchemy.create_engine(_CONNECTION_STRING, pool_size=5, max_overflow=0)
    conn = engine.connect()
    try:
        results = conn.execute(stmt)
    except Exception:
        _logger.exception("Failed to retrieve value and previous_value from statistics table")
        raise
    conn.close()
    results = results.fetchall()[0]
    return results[0], results[1]


def stats_history_main():
    """
    1. SELECT against the  statistics table, to get a snapshot of the data at that moment. 
    Based on the snapshot: 
        1. INSERT the delta between `value` and `previous_value` into  statistics_history
        2. UPDATE the previous_value in statistics table to be equal to statistics.value at snapshot 
    """

    # List of distinct statistics.keys values
    stats_key_value_list = list_stats_keys()
    # set history_ts
    stmt = sqlalchemy.select([sqlalchemy.func.now()])
    engine = sqlalchemy.create_engine(_CONNECTION_STRING, pool_size=5, max_overflow=0)
    conn = engine.connect()
    try:
        results = conn.execute(stmt)
    except Exception:
        _logger.exception("Failed to retrieve CURRENT_TIMESTAMP")
        raise
    for result in results.fetchall():
        history_ts = result[0]

    for key in stats_key_value_list:
        value, previous_value = select_from_statistics(key=key)
        insert_into_stats_history(key=key, value=value-previous_value, history_ts=history_ts)
        update_previous_value(key=key, value=value)

if __name__ == '__main__':
    stats_history_main()

# """Testing of statistics_history
# """
# import random
#
#
# def update_statistics_table():
#     """
#     Update statistics.value with a value that's 1 to 10 numbers larger
#     """
#     stats_key_value_list = _list_stats_keys()
#     for key in stats_key_value_list:
#         val = random.randint(1,10)
#         stmt = sqlalchemy.select([_STATS_TABLE.c.value]).where(_STATS_TABLE.c.key == key)
#         result = __query_execution(stmt)
#         result = int(result.fetchall()[0][0])+val
#         stmt = _STATS_TABLE.update().values(value=result).where(_STATS_TABLE.c.key == key)
#         __query_execution(stmt)
#
#
# def test_assert_previous_value_equals_value():
#     """Assert that previous_value = value"""
#     result_set = {}
#     stats_key_value_list = _list_stats_keys()
#     for key in stats_key_value_list:
#         stmt = sqlalchemy.select([_STATS_TABLE.c.value,
#                                   _STATS_TABLE.c.previous_value]).where(_STATS_TABLE.c.key == key)
#         result = __query_execution(stmt).fetchall()
#         result_set[result[0][0]] = result[0][1]
#
#     if (key == result_set[key] for key in sorted(result_set.keys())):
#         return "SUCCESS"
#     return "FAIL"
#
#
# def test_assert_previous_value_less_than_value():
#     """Assert that previous_value < value"""
#     result_set = {}
#     stats_key_value_list = _list_stats_keys()
#     for key in stats_key_value_list:
#         stmt = sqlalchemy.select([_STATS_TABLE.c.value,
#                                   _STATS_TABLE.c.previous_value]).where(_STATS_TABLE.c.key == key)
#         result = __query_execution(stmt).fetchall()
#         result_set[result[0][0]] = result[0][1]
#
#     if (key > result_set[key] for key in sorted(result_set.keys())):
#         return "SUCCESS"
#     return "FAIL"
#
#
# def stats_history_table_value():
#     delta = {}
#     stats_key_value_list = _list_stats_keys()
#     for key_value in stats_key_value_list:
#         stmt = sqlalchemy.select([_STATS_HISTORY_TABLE.c.value]).select_from(_STATS_HISTORY_TABLE).where(
#             _STATS_HISTORY_TABLE.c.key == key_value)
#         result = __query_execution(stmt).fetchall()
#         delta[key_value] = result[0][0]
#     return delta
#
# def test_main():
#     """Test verification main"""
#     delta1 = stats_history_table_value()
#     stats_history_main()
#     print('TEST A: Verify previous_value = value - ' + test_assert_previous_value_equals_value())
#     update_statistics_table()
#     print('TEST B: Verify previous_value < value - ' + test_assert_previous_value_less_than_value())
#     stats_history_main()
#     delta2 = stats_history_table_value()
#     for key in sorted(delta1.keys()):
#         if delta1[key] != delta2[key]:
#             print(key+": Stat History Updated - SUCCESS")
#         else:
#             print(key + ": Stat History Updated - FAIL")


