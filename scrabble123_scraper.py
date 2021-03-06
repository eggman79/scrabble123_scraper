#!/usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
import argparse
import urllib.parse
import re
import bs4
import urllib3

class Downloader:
    MAIN_URL = 'https://scrabble123.pl'
    WORDS_BY_LEN_URL_POSTFIX = '/slownik-scrabble'
    MAX_WORDS_IN_BUFFER = 1024

    def __init__(self, output_filename):
        self.http = urllib3.PoolManager()
        self.output = open(output_filename, 'a')
        self.words = []

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

        for a_item in body.find_all('a', {'href': True}, recursive=True):
            href = a_item['href']

            if not re.match(r"\/lista-slow-[a-z]+", href) is None:
                yield href

    def _add_word(self, word):
        self.words.append(word)

        if Downloader.MAX_WORDS_IN_BUFFER == len(self.words):
            self._flush_words()

    def _flush_words(self):
        if not self.words:
            return

        self.output.write('\n'.join(self.words) + '\n')
        self.words.clear()

    def _download_items(self, item):
        url = Downloader.MAIN_URL + urllib.parse.quote(item)

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
                    self._add_word(word)
                else:
                    text = a_item.get_text()

                    if text and text.strip() == '»':
                        next_page_url = a_item['href'].strip()

            if next_page_url is None or next_page_url == '#':
                break

            url = Downloader.MAIN_URL + urllib.parse.quote(next_page_url)

        self._flush_words()

    def download(self):
        url = Downloader.MAIN_URL + urllib.parse.quote(Downloader.WORDS_BY_LEN_URL_POSTFIX)
        content = self._get_html(url)
        tree = Downloader._html_to_tree(content)

        for item in Downloader._get_words_by_len_items(tree):
            self._download_items(item)

        self.output.close()

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('output', help='output filename', type=str)
    args = parser.parse_args()
    Downloader(args.output).download()
except SystemExit:
    pass
except:
    traceback.print_exc()
