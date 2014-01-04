
class Query(object):
    def __init__(self, filters=None, order=None, limit=None):
        self.order = order
        self.limit = limit
        self.filters = filters

    def to_json_dict(self):
        return dict(
            order=self.order,
            limit=self.limit,
            filters=self.filters
        )

    @staticmethod
    def from_json_dict(json_dict):
        return Query(**json_dict)
