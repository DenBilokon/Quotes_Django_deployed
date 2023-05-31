from pymongo import MongoClient


def get_mongodb():
    client = MongoClient("mongodb://localhost:27017")

    db = client.hw10
    return db


