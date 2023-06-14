# import os
# import django
#
# from pymongo import MongoClient
# from ..super_quotes.models import Tag, Quote, Author
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hw10_quotes.settings")
# django.setup()
#
#
# client = MongoClient("mongodb://localhost:27017")
#
# db = client.hw10
#
# authors = db.authors.find()
#
# for author in authors:
#     Author.objects.get_or_create(
#         fullname=author['fullname'],
#         date_born=author['date_born'],
#         born_location=author['born_location'],
#         bio=author['bio']
#     )
#
# quotes = db.quotes.find()
#
# for quote in quotes:
#     tags = []
#     for tag in quote['tags']:
#         t, *_ = Tag.objects.get_or_create(name=tag)
#         tags.append(t)
#
#     exist_quote = bool(len(Quote.objects.filter(quote=quote['quote'])))
#
#     if not exist_quote:
#         author = db.authors.find_one({'_id': quote['author']})
#         a = Author.objects.get(fullname=author['fullname'])
#         q = Quote.objects.create(
#             quote=quote['quote'],
#             author=a
#         )
#
#         for tag in tags:
#             q.tags.add(tag)
#
# for a in authors:
#     print(a)
#
# for a in quotes:
#     print(a)
import os
import django
import json


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hw10_quotes.settings')
django.setup()

# Імпортуємо моделі Django
from super_quotes.models import Author, Tag, Quote

def load_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def save_authors(authors_data):
    for author_data in authors_data:
        Author.objects.create(
            fullname=author_data['fullname'],
            date_born=author_data['date_born'],
            born_location=author_data['born_location'],
            bio=author_data['bio']
        )

def save_quotes(quotes_data):
    for quote_data in quotes_data:
        author_fullname = quote_data.pop('author')
        tags_data = quote_data.pop('tags', [])
        author = Author.objects.get(fullname=author_fullname) if author_fullname else None

        tags = []
        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_data)
            tags.append(tag)

        quote = Quote.objects.create(author=author, quote=quote_data['quote'])
        quote.tags.set(tags)

def import_data():
    authors_data = load_data_from_json('authors.json')
    quotes_data = load_data_from_json('quotes.json')

    save_authors(authors_data)
    save_quotes(quotes_data)

# Запускаємо функцію для імпорту даних
import_data()