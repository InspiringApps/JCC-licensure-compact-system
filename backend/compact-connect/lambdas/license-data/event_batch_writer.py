

class EventBatchWriter:
    """
    Utility class to batch event bridge event puts for better efficiency with the API
    """
    def __init__(self, client, batch_size: int = 50):
        self._client = client
        self._batch_size = batch_size
        self._batch = None
        self._count = 0
        self.failed_entry_count = 0
        self.failed_entries = None

    def _do_put(self):
        resp = self._client.put_events(
            Entries=self._batch
        )
        failure_count = resp.get('FailedEntryCount', 0)
        if failure_count > 0:
            self.failed_entry_count += failure_count
            self.failed_entries.extend((
                entry
                for entry in resp.get('Entries')
                if entry.get('ErrorCode')
            ))
        self._batch = []
        self._count = 0

    def __enter__(self):
        self._batch = []
        self._count = 0
        self.failed_entries = []
        self.failed_entry_count = 0
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self._do_put()
        if exc_val is not None:
            raise exc_val

    def put_event(self, Entry: dict):  # pylint: disable=invalid-name
        if self._batch is None:
            # Protecting ourselves from accidental misuse
            raise RuntimeError('This object must be used as a context manager')
        self._batch.append(Entry)
        self._count += 1
        if self._count >= self._batch_size:
            self._do_put()