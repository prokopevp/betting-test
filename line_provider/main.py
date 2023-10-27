import decimal
import enum
import logging
import sys
import time
from typing import Optional

import coloredlogs
from aio_pika import connect, Message, DeliveryMode
from aiormq import AMQPConnectionError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import RABBITMQ_URL

coloredlogs.install()
logging.basicConfig(level=logging.BASIC_FORMAT,
                    handlers=[logging.StreamHandler(stream=sys.stdout),
                              logging.FileHandler(filename='logs/line-provider.log')])
logger = logging.getLogger('LINE')


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


events: dict[str, Event] = {
    '1': Event(event_id='1', coefficient=1.2, deadline=int(time.time()) + 600, state=EventState.NEW),
    '2': Event(event_id='2', coefficient=1.15, deadline=int(time.time()) + 60, state=EventState.NEW),
    '3': Event(event_id='3', coefficient=1.67, deadline=int(time.time()) + 90, state=EventState.NEW)
}

app = FastAPI()


async def send_rabbitmq(msg: str):
    try:
        connection = await connect(RABBITMQ_URL)
    except AMQPConnectionError:
        logger.error('Can not make event. No connection to RabbitMQ...')
        raise HTTPException(status_code=500, detail='Cannot make event...')

    channel = await connection.channel()

    await channel.default_exchange.publish(
        Message(
            body=msg.encode('utf-8'),
            delivery_mode=DeliveryMode.PERSISTENT
        ),
        routing_key="events"
    )

    await connection.close()


@app.put('/event')
async def create_event(event: Event):
    if event.event_id not in events:
        events[event.event_id] = event
    else:
        for p_name, p_value in event.model_dump(exclude_unset=True).items():
            setattr(events[event.event_id], p_name, p_value)

    await send_rabbitmq(event.model_dump_json())

    return {'msg': 'OK'}


@app.get('/event/{event_id}', response_model=Event)
async def get_event(event_id: str):
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@app.get('/events', response_model=list[Event])
async def get_events():
    return list(e for e in events.values() if time.time() < e.deadline)
