from elasticsearch.helpers import bulk


class Bulk(object):
    """ Class for bulk actions on documents

    Allowed bulk actions are `index`, `update` and `delete`. Different actions
    can be mixed in one bulk request. Different types of documents can also be
    mixed in one bulk request.

    The Bulk class accepts various kwargs which will be passed to the bulk
    implementation of the elasticsearch client. For details see the docs
    http://elasticsearch-py.readthedocs.org/en/master/helpers.html
    """

    def __init__(self, es, **bulk_args):
        self.es = es
        self.bulk_args = bulk_args
        self.actions = []

    def index(self, doc):
        self.actions.append(
            self._get_action_base(
                'index',
                doc,
                _source=doc.get_index_body()
            )
        )

    def update(self, doc, properties=None):
        self.actions.append(
            self._get_action_base(
                'update',
                doc,
                **doc.get_update_body(properties)
            )
        )

    def delete(self, doc):
        self.actions.append(
            self._get_action_base('delete', doc)
        )

    def flush(self):
        res = bulk(self.es,
                   self.actions,
                   **self.bulk_args)
        self.actions = []
        return res

    def _get_action_base(self, action, document, **kwargs):
        res = {
            "_op_type": action,
            "_index": document.INDEX,
            "_type": document.DOC_TYPE,
            "_id": document.id,
        }
        res.update(kwargs)
        return res
