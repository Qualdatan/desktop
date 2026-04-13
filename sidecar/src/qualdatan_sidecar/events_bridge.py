# SPDX-License-Identifier: AGPL-3.0-only
"""Bruecke zwischen synchronem ``qualdatan_core.events.EventBus`` und
asynchronen SSE-Subscriptions.

Der Core emittiert Progress-Events **synchron** (siehe
:mod:`qualdatan_core.events`). SSE-Subscriber leben in einem
``asyncio``-Eventloop und brauchen eine ``async``-Quelle. Dieses Modul
bietet eine thread-/loop-sichere Bruecke:

* :func:`publish` legt ein :class:`ProgressEvent` in die
  ``asyncio.Queue`` jedes fuer ``run_id`` aktiven Subscribers.
* :func:`subscribe` ist ein ``async``-Context-Manager, der einen
  Subscriber registriert, die Queue leert und beim Verlassen wieder
  abmeldet.
* :func:`bus_for_run` liefert einen ``EventBus``, dessen Events in
  ``ProgressEvent``-Form in die Bruecke uebersetzt werden — so koennen
  existierende Core-Publisher unveraendert bleiben.

Example:
    >>> import asyncio
    >>> from qualdatan_sidecar.contract.models import ProgressEvent
    >>> async def main():
    ...     async def consumer():
    ...         async with subscribe("42") as stream:
    ...             async for evt in stream:
    ...                 return evt
    ...     task = asyncio.create_task(consumer())
    ...     await asyncio.sleep(0)
    ...     publish(ProgressEvent(event_type="started", run_id="42"))
    ...     return await task
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections import defaultdict
from typing import AsyncIterator

from qualdatan_core.events import (
    Event,
    EventBus,
    RunFinished,
    RunStarted,
    StageFinished,
    StageProgress,
    StageStarted,
)

from .contract.models import ProgressEvent

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_subscribers: dict[str, list[tuple[asyncio.AbstractEventLoop, asyncio.Queue]]] = defaultdict(
    list
)
"""Pro ``run_id``: Liste von (Loop, Queue)-Paaren. Loop wird gebraucht, um
aus beliebigen Threads via ``call_soon_threadsafe`` zu publishen."""


def _register(
    run_id: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue
) -> None:
    with _lock:
        _subscribers[run_id].append((loop, queue))


def _unregister(
    run_id: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue
) -> None:
    with _lock:
        entries = _subscribers.get(run_id)
        if not entries:
            return
        try:
            entries.remove((loop, queue))
        except ValueError:
            pass
        if not entries:
            _subscribers.pop(run_id, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def publish(event: ProgressEvent) -> None:
    """Verteilt ein :class:`ProgressEvent` an alle Subscriber der run_id.

    Thread-safe: kann aus Sync-Code in beliebigen Threads aufgerufen werden.
    Wird keine Subscription gefunden, wird das Event verworfen (Fire-and-
    forget Semantik).

    Args:
        event: Das zu publishende ProgressEvent.
    """

    with _lock:
        entries = list(_subscribers.get(event.run_id, ()))
    for loop, queue in entries:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, event)
        except RuntimeError:
            # Loop ist geschlossen — Subscriber verschwindet beim naechsten
            # Cleanup, ignorieren.
            continue


@contextlib.asynccontextmanager
async def subscribe(run_id: str) -> AsyncIterator[AsyncIterator[ProgressEvent]]:
    """Async-Context-Manager: subscribet fuer ``run_id`` und liefert einen
    Async-Iterator ueber :class:`ProgressEvent`.

    Wird der Context verlassen, wird der Subscriber deregistriert; nicht
    abgeholte Events werden verworfen.

    Example:
        >>> async with subscribe("r1") as stream:
        ...     async for evt in stream:
        ...         handle(evt)
    """

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[ProgressEvent | None] = asyncio.Queue()
    _register(run_id, loop, queue)

    async def _iter() -> AsyncIterator[ProgressEvent]:
        while True:
            evt = await queue.get()
            if evt is None:  # Sentinel -> Stream beenden
                return
            yield evt

    try:
        yield _iter()
    finally:
        _unregister(run_id, loop, queue)


def close_run(run_id: str) -> None:
    """Schliesst alle Subscriber-Streams fuer ``run_id`` mit Sentinel."""

    with _lock:
        entries = list(_subscribers.get(run_id, ()))
    for loop, queue in entries:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except RuntimeError:
            continue


# ---------------------------------------------------------------------------
# Core-Bus Adapter
# ---------------------------------------------------------------------------


def _core_event_to_progress(run_id: str, event: Event) -> ProgressEvent | None:
    """Uebersetzt ein Core-:class:`Event` in ein SSE-:class:`ProgressEvent`.

    Returns:
        ``None``, wenn der Event-Typ nicht auf ein ProgressEvent abgebildet
        wird (z.B. ``LogMessage``, ``TokensUsed``).
    """

    if isinstance(event, RunStarted):
        return ProgressEvent(
            event_type="started",
            run_id=event.run_id or run_id,
            message=event.profile or None,
        )
    if isinstance(event, RunFinished):
        return ProgressEvent(
            event_type="finished" if event.status == "done" else "failed",
            run_id=event.run_id or run_id,
            message=event.status,
        )
    if isinstance(event, StageStarted):
        return ProgressEvent(
            event_type="material_started",
            run_id=run_id,
            step=event.stage or None,
        )
    if isinstance(event, StageProgress):
        pct: float | None = None
        if event.total:
            pct = max(0.0, min(100.0, (event.done / event.total) * 100.0))
        return ProgressEvent(
            event_type="material_progress",
            run_id=run_id,
            step=event.stage or None,
            pct=pct,
            material=event.detail or None,
        )
    if isinstance(event, StageFinished):
        return ProgressEvent(
            event_type="material_finished",
            run_id=run_id,
            step=event.stage or None,
        )
    return None


def bus_for_run(run_id: str) -> EventBus:
    """Liefert einen :class:`EventBus`, der Events als ProgressEvents in die
    Bruecke der gegebenen ``run_id`` publisht.

    Der Core-Publisher kann diesen Bus an seinen RunContext haengen, ohne
    irgendetwas ueber SSE zu wissen.
    """

    bus = EventBus()

    def _forward(event: Event) -> None:
        progress = _core_event_to_progress(run_id, event)
        if progress is not None:
            publish(progress)

    bus.subscribe(_forward)
    return bus


__all__ = [
    "bus_for_run",
    "close_run",
    "publish",
    "subscribe",
]
