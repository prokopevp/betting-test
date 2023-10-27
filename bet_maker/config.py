import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, '.env'))


BET_LOG_FILENAME = "logs/bet_maker.log"

PG_USER=os.environ.get('PG_USER', 'admin')
PG_PASSWORD=os.environ.get('PG_PASSWORD', 'admin')
PG_DB=os.environ.get('PG_DB', 'betdb')
PG_HOST=os.environ.get('PG_HOST', 'localhost')
PG_PORT=os.environ.get('PG_PORT', 5431)

RABBITMQ_URL=os.environ.get("RABBITMQ_URL", "amqp://admin:admin@localhost/")

LINE_PROVIDER_URL=os.environ.get('LINE_PROVIDER_URL', 'http://localhost:8000/events')
