from dataclasses import dataclass
from typing import Any, AsyncIterator, Type
import logging

from nats.aio.client import Client as NatsClient
from nats.aio.subscription import Subscription as NatsSubscription
import nats

from event_sourcing.entity import Entity, EntityEvent

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass(frozen=True, eq=True)
class EventStoreSubscription:
    event_class: str | None = None
    event_type: Type[EntityEvent] | None = None
    entity_type: Type[Entity] | None = None
    entity_id: str | None = None

    def __post_init__(self) -> None:
        if (self.event_class is not None and self.event_type is not None) or (
            self.event_class is None and self.event_type is None
        ):
            raise (ValueError("Exactly one of 'event_class' or 'event_type' should be provided"))

    @property
    def nats_channel(self) -> str:
        if not self.event_class:
            event_class = self.event_type.__event_class__ if self.event_type else "*"
        else:
            event_class = self.event_class
        event_name = self.event_type.__name__ if self.event_type else "*"
        entity_id = self.entity_id if self.entity_id else "*"
        entity_type = self.entity_type.__name__ if self.entity_type else "*"
        return f"events.{event_class}.{entity_type}.{entity_id}.{event_name}"


class EventStoreClient:
    def __init__(
        self,
        *,
        nats_dsn: str,
        event_types: set[Type[EntityEvent]],
    ) -> None:
        self._nc: NatsClient | None = None

        self._event_types = {event_type.__name__: event_type for event_type in event_types}
        self._nats_dsn = nats_dsn
        self._nats_subscription: NatsSubscription | None = None

    async def connect(self) -> None:
        if self._nc is not None and self._nc.is_connected:
            return
        self._nc = await nats.connect(self._nats_dsn)

    async def close_subscriptions(self) -> None:
        if self._nats_subscription:
            nssub = self._nats_subscription
            self._nats_subscription = None
            await nssub.drain()

    async def disconnect(self) -> None:
        if self._nc is None or not self._nc.is_connected:
            return

        nc = self._nc
        self._nc = None

        await nc.flush()
        await nc.close()

    @property
    def is_ready(self) -> bool:
        return self._nc is not None and self._nc.is_connected and not self._nc.is_draining

    async def publish_batch(self, batch: list[EntityEvent]) -> None:
        if not self.is_ready:
            raise AssertionError()

        for event in batch:
            event_data = event.serialize()

            log.info(
                f"events.{event.__event_class__}.{event.__entity_type__}"
                f".{event.entity_id}.{type(event).__name__} ->  {event_data}"
            )
            await self._nc.publish(
                f"events.{event.__event_class__}.{event.__entity_type__}"
                f".{event.entity_id}.{type(event).__name__}",
                event_data,
            )

    async def subscribe(self, subscription: EventStoreSubscription) -> AsyncIterator[EntityEvent]:
        if not self.is_ready:
            raise AssertionError()

        self._nats_subscription = await self._nc.subscribe(subscription.nats_channel)

        async for msg in self._nats_subscription.messages:
            event_type = self._event_types.get(msg.subject.split(".")[4])
            if event_type is None:
                continue
            yield event_type.deserialise(msg.data)

    async def subscribe_with_callback(
        self,
        subscription: EventStoreSubscription,
        callback: Any,
    ) -> AsyncIterator[EntityEvent]:
        if not self.is_ready:
            raise AssertionError()

        self._nats_subscription = await self._nc.subscribe(subscription.nats_channel, cb=callback)
