import asyncio
import datetime
import decimal
import enum
import logging
import sys
from typing import List, Any

import coloredlogs
from sqlalchemy import Integer, Numeric, VARCHAR, ForeignKey, Float, select, Result, ScalarResult, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, \
    AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

from config import PG_USER, PG_PASSWORD, PG_HOST, PG_DB, PG_PORT, BET_LOG_FILENAME
from schemas import Event

coloredlogs.install()
logging.basicConfig(level=logging.BASIC_FORMAT,
                    handlers=[logging.StreamHandler(stream=sys.stdout),
                              logging.FileHandler(filename=BET_LOG_FILENAME)])
logger = logging.getLogger('DB')


class Base(AsyncAttrs, DeclarativeBase):
    pass


class BetModel(Base):
    __tablename__ = 'bet'
    bet_id: Mapped[str] = mapped_column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)

    event: Mapped['EventModel'] = relationship(back_populates='bets')
    event_id: Mapped[str] = mapped_column(ForeignKey("event.event_id"))

    amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2), nullable=False)


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class EventModel(Base):
    __tablename__ = "event"

    event_id: Mapped[str] = mapped_column(VARCHAR(256), nullable=False, unique=True, primary_key=True)
    coefficient: Mapped[decimal.Decimal] = mapped_column(Float())
    deadline: Mapped[int] = mapped_column(Integer)
    state: Mapped[int] = mapped_column(Integer)

    bets: Mapped[List['BetModel']] = relationship(back_populates='event')


# engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
# Base.metadata.create_all(engine)

engine = create_async_engine(f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}", poolclass=NullPool)


async def init_models():
    while True:
        try:
            async with engine.begin() as conn:
                logger.info('Initialize database...')
                await conn.run_sync(Base.metadata.create_all)
                break
        except ConnectionRefusedError:
            logger.info('Waiting for database connection...')
            await asyncio.sleep(5)


Session = async_sessionmaker(bind=engine, expire_on_commit=False, autocommit=False, autoflush=False, class_=AsyncSession)


async def make_bet(sess: AsyncSession, event_id: str, amount: float) -> BetModel:
    stmt = select(EventModel).filter(EventModel.event_id == event_id,
                                     EventModel.deadline > datetime.datetime.now().timestamp())
    res = await sess.execute(stmt)
    event = res.scalars().one()
    bet = BetModel(event=event, amount=amount)

    sess.add(bet)

    return bet


async def get_all_bets(sess: AsyncSession) -> Result[tuple[Any, Any]]:
    return await sess.execute(select(BetModel.bet_id, EventModel.state) \
                              .join(EventModel))


async def get_fresh_events(sess: AsyncSession) -> ScalarResult[EventModel]:
    return await sess.scalars(select(EventModel).filter(EventModel.deadline > datetime.datetime.now().timestamp()))


async def update_event(sess: AsyncSession, event: Event) -> EventModel:
    event = EventModel(
        event_id=event.event_id,
        coefficient=event.coefficient,
        deadline=event.deadline,
        state=event.state.value
    )

    await sess.merge(event)
    return event
