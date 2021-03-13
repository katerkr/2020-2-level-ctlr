"""
Crawler implementation
"""
import json
from time import sleep
import datetime
import os
import requests
from bs4 import BeautifulSoup
from article import Article
from constants import CRAWLER_CONFIG_PATH, ASSETS_PATH

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/89.0.4389.82 Safari/537.36'}


class IncorrectURLError(Exception):
    """
    Custom error
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Custom error
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Custom error
    """


class UnknownConfigError(Exception):
    """
    Most general error
    """


class Crawler:
    """
    Crawler implementation
    """

    def __init__(self, seed_urls: list, max_articles: int, max_articles_per_seed: int):
        self.seed_urls = seed_urls
        self.max_articles = max_articles
        self.max_articles_per_seed = max_articles_per_seed
        self.urls = []

    @staticmethod
    def _extract_url(article_bs):
        url_article = article_bs.find('p', class_='t-regular').find('a')
        return 'https://burunen.ru/news/' + url_article.attrs['href']

    def find_articles(self):
        """
        Finds articles
        """
        for url in self.seed_urls:
            response = requests.get(url, headers=headers)
            sleep(5)
            if not response:
                raise IncorrectURLError
            article_bs = BeautifulSoup(response.content, features='lxml')
            article_soup = article_bs.find_all('p', class_='t-regular')
            for article_bs in article_soup[:self.max_articles_per_seed]:
                self.urls.append(self._extract_url(article_bs))
                if len(self.urls) == self.max_articles:
                    break
        return self.urls

    def get_search_urls(self):
        """
        Returns seed_urls param
        """
        return self.seed_urls


class ArticleParser:
    """
    ArticleParser implementation
    """

    def __init__(self, full_url: str, article_id: int):
        self.full_url = full_url
        self.article_id = article_id
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup):
        self.article.text = article_soup.find('div', class_="text letter").text

    def _fill_article_with_meta_information(self, article_soup):
        self.article.title = article_soup.find('h1', class_='h-display').text.strip()

        for topic in article_soup.find_all('div', class_='b-caption'):
            self.article.topics.append(topic.text)

        self.article.author = article_soup.find('div', class_='credits t-caption')

        self.article.date = self.unify_date_format(article_soup.find('div', class_="b-caption").text)

    @staticmethod
    def unify_date_format(date_str):
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, "%d.%m.%Y")

    def parse(self):
        """
        Parses each article
        """
        response = requests.get(self.full_url, headers=headers)
        if not response:
            raise IncorrectURLError

        article_soup = BeautifulSoup(response.content, features='lxml')

        self._fill_article_with_text(article_soup)
        self._fill_article_with_meta_information(article_soup)
        self.article.save_raw()
        return self.article


def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    if not os.path.exists(base_path):
        os.makedirs(base_path)


def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path, 'r', encoding='utf-8') as file:
        conf = json.load(file)

    if 'base_urls' not in conf or not isinstance(conf['base_urls'], list) or\
            not all([isinstance(link, str) for link in conf['base_urls']]):
        raise IncorrectURLError

    if 'total_articles_to_find_and_parse' in conf and \
            isinstance(conf['total_articles_to_find_and_parse'], int) and \
            conf['total_articles_to_find_and_parse'] > 100:
        raise NumberOfArticlesOutOfRangeError

    if 'max_number_articles_to_get_from_one_seed' not in conf or\
            not isinstance(conf['max_number_articles_to_get_from_one_seed'], int) or\
            'total_articles_to_find_and_parse' not in conf or\
            not isinstance(conf['total_articles_to_find_and_parse'], int):
        raise IncorrectNumberOfArticlesError

    return conf['base_urls'], conf['total_articles_to_find_and_parse'], conf[
        'max_number_articles_to_get_from_one_seed']


if __name__ == '__main__':
    # YOUR CODE HERE
    seed_urls_ex, max_articles_ex, max_articles_per_seed_ex = validate_config(CRAWLER_CONFIG_PATH)
    crawler = Crawler(seed_urls_ex, max_articles_ex, max_articles_per_seed_ex)

    prepare_environment(ASSETS_PATH)

    for ind, article_url in enumerate(crawler.urls):
        parser = ArticleParser(full_url=article_url, article_id=ind + 1)
        parser.parse()
