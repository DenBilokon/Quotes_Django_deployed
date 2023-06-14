import datetime
import re
import environ
import openai

import requests
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Quote, Author, Tag

from .forms import AuthorForm, QuoteForm, TagForm

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')
OPENAI_KEY = env('OPENAI_KEY')


def home(request, page=1):
    quotes = Quote.objects.all()
    per_page = 5
    paginator = Paginator(list(quotes), per_page)
    quotes_on_page = paginator.page(page)
    top_tags = Quote.objects.values('tags__name').annotate(quote_count=Count('tags__name')).order_by('-quote_count')[
               :10]
    war_info = war_spider()
    return render(request, "super_quotes/index.html", context={"quotes": quotes_on_page, 'top_tags': top_tags,
                                                               'war_info': war_info})


def author_about(request, _id):
    author = Author.objects.get(pk=_id)
    return render(request, 'super_quotes/author.html', context={'author': author})


def question_to_ai(request, _id):
    author = Author.objects.get(pk=_id)
    openai.api_key = OPENAI_KEY

    question = request.POST.get('question')
    prompt = f'You are a historical person - {author}. I will ask you a question and you have to answer it, ' \
             f'as if you were this historical person. Also, you should know everything about yourself and answer ' \
             f'clearly and a little defiantly, but without exaggeration' \
             f'Only truth. Use emoticons to decorate the dialogue. So, the question is - {question}'

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=50,
        temperature=0.7,
        n=1,
        stop=None,
        echo=True
    )

    if 'choices' in response and len(response.choices) > 0:
        answer = response.choices[0].text.strip()
        response_html = answer.replace(prompt, "")
    else:
        response_html = None

    return render(request, 'super_quotes/question_response.html', context={'author': author,
                                                                           'answer_for_user': response_html})


@login_required
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            new_quote = form.save()
            return redirect(to='super_quotes:home')
        else:
            return render(request, 'super_quotes/add_quote.html',
                          context={'form': QuoteForm, 'message': "Форма невірна"})
    return render(request, 'super_quotes/add_quote.html', context={'form': QuoteForm()})


@login_required
def add_author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            new_author = form.save()
            return redirect(to='super_quotes:home')
        else:
            return render(request, 'super_quotes/add_author.html',
                          context={'form': AuthorForm, 'message': "Форма невірна"})
    return render(request, 'super_quotes/add_author.html', context={'form': AuthorForm()})


@login_required
def add_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_tag = form.save()
            return redirect(to='super_quotes:home')
        else:
            return render(request, 'super_quotes/add_tag.html',
                          context={'form': TagForm, 'message': "Форма невірна"})
    return render(request, 'super_quotes/add_tag.html', context={'form': TagForm})


def find_tag(request, _id):
    per_page = 5
    if isinstance(_id, int):
        quotes = Quote.objects.filter(tags=_id).all()
    elif isinstance(_id, str):
        tag_id = Tag.objects.filter(name=_id).first()
        quotes = Quote.objects.filter(tags=tag_id).all()
    paginator = Paginator(list(quotes), per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    top_tags = Quote.objects.values('tags__id', 'tags__name').annotate(quote_count=Count('tags__name')).order_by(
        '-quote_count')[:10]

    return render(request, 'super_quotes/find_tag.html',
                  context={'quotes': page_obj, 'tag_name': _id, 'top_tags': top_tags})


def search_quotes(request):
    query = request.GET.get('q')
    quotes = Quote.objects.filter(
        Q(tags__name__icontains=query) |
        Q(quote__icontains=query) |
        Q(author__fullname__icontains=query)
    ).distinct()

    return render(request, 'super_quotes/search_quotes.html', context={'quotes': quotes, 'query': query})


def parse_quotes(request):
    base_url = 'http://quotes.toscrape.com'

    def get_author_urls():
        author_links = []
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = soup.find_all('div', class_='quote')
        for q in quotes:
            author_links.append(q.find("a", href=True).get('href'))
        return author_links

    def quote_spider():
        created_quotes = []
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select('div[class=col-md-8] div[class=quote]')
        for el in content:
            quote_text = el.find('span', attrs={'class': 'text'}).text
            author_fullname = el.find('small', attrs={'class': 'author'}).text
            author, created = Author.objects.get_or_create(fullname=author_fullname)

            tags = (list(filter(bool, [t.text.strip() for t in el.find('div', class_='tags').find_all('a')])))

            new_quote, created = Quote.objects.get_or_create(quote=quote_text, author=author)
            if created:
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    new_quote.tags.add(tag)
            new_quote.save()
            created_quotes.append(new_quote)
        return created_quotes

    def author_spider():
        author_links = get_author_urls()
        created_authors = []
        for link in author_links:
            response = requests.get(base_url + link)
            soup = BeautifulSoup(response.text, 'lxml')
            content = soup.select('div[class=container] div[class=author-details]')
            for el in content:
                fullname = el.find('h3', attrs={'class': 'author-title'}).text.strip()
                date_born = el.find('span', attrs={'class': 'author-born-date'}).text.strip()
                born_location = el.find('span', attrs={'class': 'author-born-location'}).text.strip()
                bio = el.find('div', attrs={'class': 'author-description'}).text.strip()
                author, created = Author.objects.get_or_create(fullname=fullname, date_born=date_born,
                                                               born_location=born_location,
                                                               bio=bio)
                author.save()
                created_authors.append(author)
        return created_authors

    def parsing():
        return author_spider(), quote_spider()

    return render(request, 'super_quotes/parse_quotes.html', context={'final_parse': parsing,
                                                                      'base_url': base_url})


def war_spider():
    base_url = 'https://index.minfin.com.ua/ua/russian-invading/casualties'
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find_all('div', class_='casualties')
    numbers = re.findall(r'\d+(?=\s*<small>\(\+\d+\)</small></li>|</li>)', str(content[0]))

    war_dict = {
        'date': datetime.date.today().strftime("%d.%m.%Y"),
        'tanks': int(numbers[0]),
        'bbm': int(numbers[1]),
        'artillery': int(numbers[2]),
        'rszw': int(numbers[3]),
        'ppo': int(numbers[4]),
        'planes': int(numbers[5]),
        'helicopters': int(numbers[6]),
        'drones': int(numbers[7]),
        'rockets': int(numbers[8]),
        'ships': int(numbers[9]),
        'vehicles': int(numbers[10]),
        'auto': int(numbers[11]),
        'orks': int(re.findall(r'Особовий склад\s*—\s*близько\s*(\d+)\s*<span', str(content[0]))[0])
    }
    return war_dict
