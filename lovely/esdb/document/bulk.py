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

    def store(self, doc):
        """Store a document using the bulk

        Index the document.
        See also the comments for the Document.store about using the update
        API.
        """
        self._store_index(doc)

    def delete(self, doc):
        """Delete a document using the bulk
        """
        self.actions.append(
            self._get_action_base('delete', doc)
        )

    def update_or_create(self, doc, properties=None):
        """Update or create a document using the bulk

        Uses `update_or_create` to insert the document into the bulk.
        """
        self.actions.append(
            self._get_action_base(
                'update',
                doc,
                _retry_on_conflict=5,
                **doc._get_update_or_create_body(properties)
            )
        )

    def flush(self):
        """Execute the actions of the bulk
        """
        if self.actions:
            res = bulk(self.es,
                       self.actions,
                       **self.bulk_args)
            self.actions = []
            return res

    def _store_index(self, doc):
        """Index a new document
        """
        self.actions.append(
            self._get_action_base(
                'index',
                doc,
                _source=doc._get_store_index_body()
            )
        )

    def _store_update(self, doc):
        """Update an existing document
        """
        changes = doc._get_store_update_doc()
        if not changes:
            # no changes no action
            return
        self.actions.append(
            self._get_action_base(
                'update',
                doc,
                _retry_on_conflict=5,
                doc=changes
            )
        )

    def _get_action_base(self, action, document, **kwargs):
        res = {
            "_op_type": action,
            "_index": document.INDEX,
            "_type": document.DOC_TYPE,
            "_id": document.get_primary_key(set_after_read=True),
        }
        res.update(kwargs)
        return res
