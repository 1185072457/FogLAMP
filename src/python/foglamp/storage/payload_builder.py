# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Storage layer python client payload builder
"""

__author__ = "Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

from collections import OrderedDict
import json
import urllib.parse
import numbers

from foglamp import logger


_LOGGER = logger.setup(__name__)


class PayloadBuilder(object):
    """ Payload Builder to be used in Python client  for Storage Service

    """

    # TODO: Add json validator
    ''' Ref: https://docs.google.com/document/d/1qGIswveF9p2MmAOw_W1oXpo_aFUJd3bXBkW563E16g0/edit#
        Ref: http://json-schema.org/
        Ref: http://json-schema.org/implementations.html#validators
    '''
    # TODO: Add tests

    query_payload = None

    def __init__(self, initial_payload=OrderedDict()):
        # TODO: Investigate why simple "self.__class__.query_payload = initial_payload" is not working
        self.__class__.query_payload = initial_payload if len(initial_payload) else OrderedDict()

    @staticmethod
    def verify_condition(arg):
        retval = False
        if isinstance(arg, list):
            if len(arg) == 3:
                # TODO: Implement LIKE and IN later when support becomes available in storage service
                if arg[1] in ['<', '>', '=', '>=', '<=', '!=']:
                    retval = True
        return retval

    @staticmethod
    def verify_aggregation(arg):
        retval = False
        if isinstance(arg, list):
            if len(arg) == 2:
                if arg[0] in ['min', 'max', 'avg', 'sum', 'count']:
                    retval = True
        return retval

    @staticmethod
    def verify_orderby(arg):
        retval = False
        if isinstance(arg, list):
            if len(arg) == 1:
                arg.append('asc')

            if len(arg) == 2:
                if arg[1].upper() in ['ASC', 'DESC']:
                    retval = True
        return retval

    @classmethod
    def ALIAS(cls, *args):
        raise NotImplementedError("To be implemented")

    @classmethod
    def SELECT(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        if len(args) > 0:
            cls.query_payload.update({"columns": ','.join(args)})
        return cls

    @classmethod
    def SELECT_ALL(cls):
        cls.query_payload.update({"columns": '*'})
        return cls

    @classmethod
    def FROM(cls, tbl_name):
        cls.query_payload.update({"table": tbl_name})
        return cls

    @classmethod
    def UPDATE_TABLE(cls, tbl_name):
        return cls.FROM(tbl_name)

    @classmethod
    def COLS(cls, kwargs):
        values = {}
        for key, value in kwargs.items():
            values.update({key: value})
        return values

    @classmethod
    def SET(cls, **kwargs):
        cls.query_payload.update({"values": cls.COLS(kwargs)})
        return cls

    @classmethod
    def INSERT(cls, **kwargs):
        cls.query_payload.update(cls.COLS(kwargs))
        return cls

    @classmethod
    def INSERT_INTO(cls, tbl_name):
        return cls.FROM(tbl_name)

    @classmethod
    def DELETE(cls, tbl_name):
        return cls.FROM(tbl_name)

    @classmethod
    def WHERE(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        print(args)
        for arg in args:
            condition = {}
            if cls.verify_condition(arg):
                condition.update({"column": arg[0], "condition": arg[1], "value": arg[2]})
                if 'where' in cls.query_payload:
                    cls.query_payload['where'].update({"and": condition})
                else:
                    cls.query_payload.update({"where": condition})
        return cls

    @classmethod
    def AND_WHERE(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        print(args)
        for arg in args:
            condition = {}
            if cls.verify_condition(arg):
                condition.update({"column": arg[0], "condition": arg[1], "value": arg[2]})
                if 'where' in cls.query_payload:
                    cls.query_payload['where'].update({"and": condition})
                else:
                    cls.query_payload.update({"where": condition})
        return cls

    @classmethod
    def OR_WHERE(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        for arg in args:
            condition = {}
            if cls.verify_condition(arg):
                condition.update({"column": arg[0], "condition": arg[1], "value": arg[2]})
                if 'where' in cls.query_payload:
                    cls.query_payload['where'].update({"or": condition})
                else:
                    cls.query_payload.update({"where": condition})
        return cls

    @classmethod
    def GROUP_BY(cls, *args):
        cls.query_payload.update({"group": ', '.join(args)})
        return cls

    @classmethod
    def AGGREGATE(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        for arg in args:
            aggregate = {}
            if cls.verify_aggregation(arg):
                aggregate.update({"operation": arg[0], "column": arg[1]})
                if 'aggregate' in cls.query_payload:
                    if not isinstance(cls.query_payload['aggregate'], list):
                        cls.query_payload['aggregate'] = [cls.query_payload.get('aggregate')]
                    cls.query_payload['aggregate'].append(aggregate)
                else:
                    cls.query_payload.update({"aggregate": aggregate})
        return cls

    @classmethod
    def HAVING(cls):
        raise NotImplementedError("To be implemented")

    @classmethod
    def LIMIT(cls, arg):
        if isinstance(arg, numbers.Real):
            cls.query_payload.update({"limit": arg})
        return cls

    @classmethod
    def OFFSET(cls, arg):
        if isinstance(arg, numbers.Real):
            cls.query_payload.update({"skip": arg})
        return cls

    SKIP = OFFSET

    @classmethod
    def ORDER_BY(cls, arg, *args):
        # Pass multiple arguments in a single tuple also. Useful when called from external process i.e. api, test.
        args = (arg,) + args if not isinstance(arg, tuple) else arg
        for arg in args:
            sort = {}
            if cls.verify_orderby(arg):
                sort.update({"column": arg[0], "direction": arg[1]})
                if 'sort' in cls.query_payload:
                    if not isinstance(cls.query_payload['sort'], list):
                        cls.query_payload['sort'] = [cls.query_payload.get('sort')]
                    cls.query_payload['sort'].append(sort)
                else:
                    cls.query_payload.update({"sort": sort})
        return cls

    @classmethod
    def payload(cls):
        return json.dumps(cls.query_payload, sort_keys=True)

    @classmethod
    def chain_payload(cls):
        """
        Sometimes, we may want to create payload incremently, based upon some conditions.
        This method will come handy in such Use cases.
        e.g. core/scheduler.py->get_tasks()
        """
        return cls.query_payload

    @classmethod
    def query_params(cls):
        where = cls.query_payload['where']
        query_params = OrderedDict({where['column']: where['value']})
        for key, value in where.items():
            if key == 'and':
                query_params.update({value['column']: value['value']})
        return urllib.parse.urlencode(query_params)
