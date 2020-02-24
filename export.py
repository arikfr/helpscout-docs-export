import os
import codecs
import requests
import yaml
import html2text
import json
from decouple import config
from pprint import pprint

API_KEY = config('HELPSCOUT_API_KEY')


class HelpScout(object):
    def __init__(self, api_key):
        self.s = requests.Session()
        self.s.auth = (api_key, 'x')
        self._collections = None
        self._categories = None

    @property
    def collections(self):
        if self._collections is None:
            # TODO: support pagination?
            response = self.s.get('https://docsapi.helpscout.net/v1/collections')
            self._collections = {}
            for collection in  response.json()['collections']['items']:
                self._collections[collection['id']] = collection

        return self._collections

    @property
    def categories(self):
        if self._categories is None:
            self._categories = {}
            for collection in self.collections.keys():
                url = 'https://docsapi.helpscout.net/v1/collections/{id}/categories'.format(id=collection)
                categories = self.s.get(url).json()['categories']['items']
                for category in categories:
                    self._categories[category['id']] = category

        return self._categories

    def get_collection_articles(self, collection_id, status='published'):
        params = {
            'pageSize': 100, 
            'status': status,
        }
        url = 'https://docsapi.helpscout.net/v1/collections/{id}/articles'.format(id=collection_id)
        response = self.s.get(url, params=params)
        if response.json()['articles']['pages'] > 1:
            i = 2
            items = response.json()['articles']['items']
            while i < response.json()['articles']['pages'] + 1:
                params = {
                    'pageSize': 100, 
                    'status': status,
                    'page': i
                }
                response = self.s.get(url, params=params)
                items = items + response.json()['articles']['items']
                i += 1
            return items
        else:
          response = self.s.get(url, params=params)
          return response.json()['articles']['items']

    def get_article(self, article_id):
        url = 'https://docsapi.helpscout.net/v1/articles/{id}'.format(id=article_id)
        response = self.s.get(url)
        article = response.json().get('article')
        if article is None:
            print response.status_code
            print response.json()
        article['collection'] = self.collections[article['collectionId']]
        article['categories'] = map(lambda c: self.categories[c]['slug'], article['categories'])
        return article


def metadata_to_frontmatter(metadata):
    frontmatter = '---\n{yaml}---\n'.format(yaml=yaml.safe_dump(metadata, default_flow_style=False))
    return frontmatter


def html_to_markdown(html):
    h = html2text.HTML2Text()
    return h.handle(html)

def markdown_from_article(article):
    body = html_to_markdown(article['text'])
    metadata = {
        'collection': article['collection']['slug'],
        'categories': article['categories'],
        'keywords': article['keywords'],
        'name': article['name'],
        'helpscout_url': article['publicUrl'],
        'slug': article['slug'],
    }

    return metadata_to_frontmatter(metadata) + body


def write_article(article):
    path = 'articles/{}'.format(article['collection']['slug'])
    filename = '{}/{}.md'.format(path, article['slug'])

    try:
        os.mkdir(path)
    except OSError:
        # directory exists. I hope. should probably check for explict error code
        pass

    with codecs.open(filename, "w", "utf-8") as f:
        f.write(markdown_from_article(article))


def export(h):
    try:
        os.mkdir('articles')
    except OSError:
        # directory exists. I hope. should probably check for explict error code
        pass

    for collection in h.collections.keys():
        articles = h.get_collection_articles(collection)
        for article_id in map(lambda a: a['id'], articles):
            article = h.get_article(article_id)
            write_article(article)


def export_metadata(h):
    with codecs.open('articles/collections.json', 'w', 'utf-8') as f:
        json.dump(h.collections, f, ensure_ascii=False, indent=4)

    with codecs.open('articles/categories.json', 'w', 'utf-8') as f:
        json.dump(h.categories, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    h = HelpScout(API_KEY)
    export(h)
    export_metadata(h)
