import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
TEXTGRID_DIR = os.path.join(DATA_DIR, 'textgrids')

MONGO_URI = 'mongodb://localhost:27017/'

USE_MONGO_MOCK = True  # Set to False to use real MongoDB
