import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, '.env'))

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', "amqp://admin:admin@localhost/")