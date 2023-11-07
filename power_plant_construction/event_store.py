from event_sourcing.event_store_client import EventStoreClient

_EVENT_STORE_CLIENT: EventStoreClient | None = None


def get_event_store() -> EventStoreClient:
    if _EVENT_STORE_CLIENT is None:
        raise AssertionError()
    return _EVENT_STORE_CLIENT


def set_event_store(event_store: EventStoreClient) -> None:
    global _EVENT_STORE_CLIENT  # pylint: disable=global-statement
    if _EVENT_STORE_CLIENT is not None:
        raise AssertionError()

    _EVENT_STORE_CLIENT = event_store
