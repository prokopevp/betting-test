import asyncio
import json
import logging
import sys
from json import JSONDecodeError

import coloredlogs
from aio_pika import connect, IncomingMessage, connect_robust
from aiormq import AMQPConnectionError

from config import BET_LOG_FILENAME, RABBITMQ_URL

coloredlogs.install()
logging.basicConfig(level=logging.BASIC_FORMAT,
                    handlers=[logging.StreamHandler(stream=sys.stdout),
                              logging.FileHandler(filename=BET_LOG_FILENAME)])
logger = logging.getLogger('PIKA CLIENT')


class PikaClient:

    def __init__(self, process_callable):
        self.process_callable = process_callable

    async def consume(self, loop=None):
        """
        Слушатель событий с line-provider
        """
        while True:
            try:
                connection = await connect_robust(RABBITMQ_URL, loop=loop, future=False)

                break
            except AMQPConnectionError:
                logger.info('Wait for RabbitMQ connection...')
                await asyncio.sleep(5)

        # Добавление слушателя при переподключении
        connection.reconnect_callbacks.add(lambda sender: asyncio.get_event_loop().create_task(self.consume()))
        channel = await connection.channel()
        queue = await channel.declare_queue('events', durable=True)
        await queue.consume(self.process_incoming_message, no_ack=False)
        logger.info('Established pika async listener')

        return connection

    async def process_incoming_message(self, message: IncomingMessage):
        """
        Первичная обработка сообщений с RabbitMQ
        и запуск процесса для работы с ними.
        """
        await message.ack()

        logger.info(f'Message from RabbitMQ')
        if message.body:
            try:
                body_data = json.loads(message.body)
                await self.process_callable(body_data)
            except JSONDecodeError:
                logger.exception('Message is not a valid JSON...')

