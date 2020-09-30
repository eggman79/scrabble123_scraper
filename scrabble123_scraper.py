#!/usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
import argparse
import urllib.parse
import re
import bs4
import urllib3

class Downloader:
    main_url = 'https://scrabble123.pl'
    words_by_len_url_postfix = '/slownik-scrabble'

    def __init__(self, output_filename):
        self.http = urllib3.PoolManager()
        self.output = open(output_filename, 'a')

    def _get_html(self, url):
        resp = self.http.request('GET', url)

        if not resp is None:
            return resp.data.decode('utf-8')

        return None

    @staticmethod
    def _html_to_tree(html):
        return bs4.BeautifulSoup(html, 'html.parser')

    @staticmethod
    def _get_words_by_len_items(tree):
        body = tree.body
        items = []

        for a_item in body.find_all('a', {'href': True}, recursive=True):
            href = a_item['href']
            if not re.match(r"\/lista-slow-[a-z]+", href) is None:
                items.append(href)

        return items

    def _download_items(self, item):
        url = Downloader.main_url + urllib.parse.quote(item)

        while True:
            content = self._get_html(url)
            tree = Downloader._html_to_tree(content)
            next_page_url = None

            for a_item in tree.find_all('a', {'href': True}, recursive=True):
                href = a_item['href']
                match = re.match(r"\/slownik-scrabble\/([^$]+$)", href)

                if not match is None:
                    word = urllib.parse.unquote(match.group(1))
                    print('page: %s word: %s' % (url, word))
                    self.output.write(word + '\n')
                elif a_item.get_text() and a_item.get_text().strip() == '»':
                    next_page_url = a_item['href'].strip()

            if next_page_url is None or next_page_url == '#':
                break

            url = Downloader.main_url + urllib.parse.quote(next_page_url)

    def download(self):
        url = Downloader.main_url + urllib.parse.quote(Downloader.words_by_len_url_postfix)
        content = self._get_html(url)
        tree = Downloader._html_to_tree(content)
        items = Downloader._get_words_by_len_items(tree)

        for item in items:
            self._download_items(item)

        self.output.close()

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('output', help='output filename with words', type=str)
    args = parser.parse_args()
    Downloader(args.output).download()
except SystemExit:
    pass
except:
    traceback.print_exc()
