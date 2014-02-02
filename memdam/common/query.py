
# pylint: disable=W0401,W0622,W0614
from funcy import *

class Query(object):
    """
    Represents a query to the event archive

    :attr filters: the set of constraints for this query
    :type filters: iterable(QueryFilter)
    :attr order: a specification of the ordering in which events should be returned
    :type order: tuple(tuple(unicode, boolean), ...)
    :attr limit: the max amount of events to return
    :type limit: int
    """
    def __init__(self, filters=None, order=None, limit=None):
        if filters == None:
            filters = ()
        self.order = order
        self.limit = limit
        self.filters = tuple(filters)

    def to_json_dict(self):
        """
        Convert from a Query object to JSON

        :returns: a dict ready for json serialization
        :rtype: dict
        """
        encoded_filters = (f.to_json_dict() for f in self.filters)
        if len(encoded_filters) <= 0:
            encoded_filters = None
        return select(lambda (k, v): v != None, dict(
            order=self.order,
            limit=self.limit,
            filters=encoded_filters
        ))

    @staticmethod
    def from_json_dict(json_dict):
        """
        Convert from JSON to a Query object.

        :param json_dict: the decoded JSON data
        :type  json_dict: dict
        :returns: the query that this JSON represents
        :rtype: memdam.common.query.Query
        """
        order = json_dict.get('order', None)
        limit = json_dict.get('limit', None)
        filters = json_dict.get('filters', None)
        decoded_filters = (QueryFilter.from_json_dict(f) for f in filters)
        return Query(filters=decoded_filters, order=order, limit=limit)

#TODO (security): be more strict about acceptable operators and strings
class QueryFilter(object):
    """
    Limit the events returned by a Query to a matching subset

    :attr lhs: left hand side of a comparison
    :type lhs: QueryFilter|unicode
    :attr operator: the actual comparison to perform.
    :type operator: string
    :attr rhs: right hand side of a comparison
    :type rhs: QueryFilter|unicode
    """

    def __init__(self, lhs, operator, rhs):
        assert lhs != None
        assert operator != None
        assert rhs != None
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs

    def to_json_dict(self):
        """
        Convert from a QueryFilter object to JSON

        :returns: a dict ready for json serialization
        :rtype: dict
        """
        encoded_lhs = _possibly_encode(self.lhs)
        encoded_rhs = _possibly_encode(self.rhs)
        return dict(
            lhs=encoded_lhs,
            operator=self.operator,
            rhs=encoded_rhs
        )

    @staticmethod
    def from_json_dict(json_dict):
        """
        Convert from JSON to a QueryFilter object.

        :param json_dict: the decoded JSON data
        :type  json_dict: dict
        :returns: the filter that this JSON represents
        :rtype: memdam.common.query.QueryFilter
        """
        lhs = json_dict['lhs']
        operator = json_dict['operator']
        rhs = json_dict['rhs']
        decoded_lhs = _possibly_decode(lhs)
        decoded_rhs = _possibly_decode(rhs)
        return QueryFilter(decoded_lhs, operator, decoded_rhs)

def _possibly_encode(arg):
    """Convert to JSON if this is a QueryFilter, otherwise return"""
    if isinstance(arg, QueryFilter):
        return arg.to_json_dict()
    return arg

def _possibly_decode(arg):
    """Convert from JSON if this is a QueryFilter, otherwise return"""
    if isinstance(arg, dict):
        return QueryFilter.from_json_dict(arg)
    return arg
