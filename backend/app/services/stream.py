from __future__ import annotations

import asyncio
import json
import structlog
from uuid import UUID
from typing import Any, AsyncGenerator

from app.redis_.client import get_redis_client

logger = structlog.get_logger(__name__)


class StreamService:
    """Manages publishing and subscribing to real-time research session events via Redis Pub/Sub."""

    def __init__(self) -> None:
        self.client = get_redis_client()
        self.prefix = "dr:pubsub"

    def _get_channel(self, session_id: UUID) -> str:
        """Construct the Redis channel name for a research session."""
        return f"{self.prefix}:{session_id}"

    async def publish_event(self, session_id: UUID, event_type: str, data: dict[str, Any]) -> bool:
        """Publish a structured event payload to the session's Redis channel."""
        channel = self._get_channel(session_id)
        payload = {
            "event": event_type,
            "data": data,
        }
        try:
            serialized = json.dumps(payload, default=str)
            logger.debug(
                "Publishing stream event to Redis Pub/Sub",
                channel=channel,
                event_type=event_type,
            )
            # Publish returns the number of active subscribers
            subscribers = await self.client.publish(channel, serialized)
            logger.debug("Event published successfully", subscribers=subscribers)
            return True
        except Exception as e:
            logger.error("Failed to publish event to Redis Pub/Sub", channel=channel, error=str(e))
            return False

    async def subscribe_session(
        self, session_id: UUID, heartbeat_interval: float = 5.0
    ) -> AsyncGenerator[str, None]:
        """Subscribe to a session's channel and yield formatted SSE events.

        Yields heartbeat 'ping' events periodically to prevent gateway/proxy timeouts.
        Cleans up the subscription gracefully on client disconnect or cancellation.
        """
        channel = self._get_channel(session_id)
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)

        logger.info(
            "Client subscribed to research session stream",
            session_id=str(session_id),
            channel=channel,
        )

        try:
            # Yield initial connection confirmation event
            yield f"event: connected\ndata: {json.dumps({'status': 'subscribed'})}\n\n"

            # We use an async loop with a timeout to support heartbeat events
            while True:
                try:
                    # Wait for message with a timeout corresponding to the heartbeat interval
                    # pubsub.get_message() checks for new messages without locking if timeout=0,
                    # but wait_for_message lets us sleep efficiently until a message arrives.
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=heartbeat_interval),
                        timeout=heartbeat_interval,
                    )

                    if message and message["type"] == "message":
                        raw_data = message["data"]
                        payload = json.loads(raw_data)
                        event_type = payload.get("event", "message")
                        data_payload = payload.get("data", {})

                        logger.debug(
                            "Yielding event downstream",
                            session_id=str(session_id),
                            event=event_type,
                        )
                        # Format as SSE standard protocol
                        yield f"event: {event_type}\ndata: {json.dumps(data_payload)}\n\n"

                        # If this is a terminal event, gracefully terminate the stream
                        if event_type in ("completed", "failed", "cancelled"):
                            logger.info(
                                "Terminal event received. Closing stream.",
                                session_id=str(session_id),
                                event=event_type,
                            )
                            break

                except asyncio.TimeoutError:
                    # Heartbeat interval expired with no new events. Yield a heartbeat ping.
                    logger.debug("Emitting SSE heartbeat ping", session_id=str(session_id))
                    yield "event: ping\ndata: {\"heartbeat\": true}\n\n"

        except asyncio.CancelledError:
            logger.info("SSE Stream subscription cancelled by client connection loss", session_id=str(session_id))
            raise

        except Exception as e:
            logger.error("Error in SSE subscription loop", session_id=str(session_id), error=str(e))
            yield f"event: error\ndata: {json.dumps({'message': f'Stream connection error: {str(e)}'})}\n\n"

        finally:
            # Clean up Redis pubsub connections gracefully
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                logger.info(
                    "Redis Pub/Sub subscription cleaned up successfully",
                    session_id=str(session_id),
                )
            except Exception as e:
                logger.error("Error cleaning up pubsub subscription", session_id=str(session_id), error=str(e))
