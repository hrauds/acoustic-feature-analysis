from pymongo import MongoClient
from config import MONGO_URI


class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['speech_analysis']
        self.recordings_col = self.db['recordings']
        self.words_col = self.db['words']
        self.phonemes_col = self.db['phonemes']
