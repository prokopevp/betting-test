import asyncio
import json
import logging
import sys

import coloredlogs
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

import db
from config import BET_LOG_FILENAME, LINE_PROVIDER_URL
from db import engine, Session
from pika_client import PikaClient
from schemas import Event, Bet

coloredlogs.install()
logging.basicConfig(level=logging.BASIC_FORMAT,
                    handlers=[logging.StreamHandler(stream=sys.stdout),
                              logging.FileHandler(filename=BET_LOG_FILENAME)])
logger = logging.getLogger('BET API')


class FastAPIWithAioPika(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pika_client = PikaClient(self.update_or_create_line_event)

    @classmethod
    async def update_or_create_line_event(cls, event_data: dict):
        try:
            event = Event(**event_data)
            async with Session() as sess:
                await db.update_event(sess, event)
                await sess.commit()
        except ValidationError as e:
            logger.error(e)


app = FastAPIWithAioPika()
http_client = AsyncClient()


async def init_line_events():
    try:
        res = await http_client.get(LINE_PROVIDER_URL)
        if res.status_code != 200:
            return

        async with Session() as sess:
            for event_data in res.json():
                event = Event(**event_data)
                await db.update_event(sess, event)
            await sess.commit()
        logger.info('Events from line-provider initialized...')
    except ConnectionRefusedError:
        return


@app.on_event('startup')
async def startup():
    await db.init_models()
    await init_line_events()
    loop = asyncio.get_event_loop()
    task = loop.create_task(app.pika_client.consume(None))
    await task
    logger.info('Events consumer added')


@app.post('/bet')
async def make_bet(bet: Bet):
    async with Session() as sess:
        try:
            applied_bet = await db.make_bet(sess, bet.event_id, bet.amount)
            await sess.commit()
            await sess.refresh(applied_bet)

            return {'bet_id': applied_bet.bet_id}
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Event expired or not found")


@app.get('/bets')
async def get_all_bets():
    async with Session() as sess:
        bets = await db.get_all_bets(sess)
        return [{'bet_id': b[0], 'state': b[1]} for b in bets]


@app.get('/events')
async def get_fresh_events():
    async with Session() as sess:
        return [Event.model_validate(m).model_dump() for m in await db.get_fresh_events(sess)]
