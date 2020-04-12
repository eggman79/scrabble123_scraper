#!/usr/bin/python3

import os
import os.path
import re
import urllib.parse
import sqlite3
import logging

from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

class WordsDownloader:
    def __init__(self, alphabet):
        self.alphabet = alphabet
        self.href_regex = re.compile(r'\/slownik-scrabble\/([' + self.alphabet + r']+)')
        self.value_regex = re.compile(r'([' + self.alphabet + r']+)\s+[\d]+')
        self.request_header = {'User-Agent': 'Mozilla/5.0'}

    def _make_request(self, letters):
        url = 'https://scrabble123.pl/slowa-z-liter/' + urllib.parse.quote_plus(letters)
        logging.info('request: %s', url)
        return Request(url, headers=self.request_header)

    def _get_html_for_letters(self, letters):
        return urlopen(self._make_request(letters), timeout=10).read()

    def get_words(self, letters):
        html = self._get_html_for_letters(letters)
        parser = BeautifulSoup(html, 'html.parser')
        words = None

        for aitem in parser.find_all('a', href=True):
            href_match = self.href_regex.match(aitem['href'])

            if href_match is None:
                continue

            value = aitem.get_text()

            if value is None:
                continue

            value_match = self.value_regex.match(value)

            if value_match is None:
                continue

            if href_match.group(1) == value_match.group(1):
                if words is None:
                    words = []
                words.append(href_match.group(1))

        return words

class Db:
    def __init__(self, db_name):
        self.db_name = db_name
        new_db = not os.path.exists(self.db_name)
        self.conn = sqlite3.connect(self.db_name)

        if new_db:
            try:
                cur = self.conn.cursor()
                cur.execute('create table words(word text)')
                cur.execute('create unique index words_word on words(word)')
                cur.execute('create table last_letters(letters text)')
                cur.execute("insert into last_letters values('')")
                self.conn.commit()
            except:
                self.conn.rollback()
                raise Exception('database creation error')

    def last_letters(self):
        cur = self.conn.cursor()
        cur.execute('select letters from last_letters')
        rows = cur.fetchall()

        if rows is None or len(rows) != 1:
            raise Exception('database last_letters error')

        result = rows[0][0]

        if not result:
            return None

        return result

    def save_words_and_letters(self, words, letters):
        try:
            cur = self.conn.cursor()

            if not words is None:
                for word in words:
                    cur.execute("insert into words(word) select '" + word + "' where not exists(select 1 from words where word = '" + word + "')")

            cur.execute("update last_letters set letters = '" + letters + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
            raise

class Main:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.alphabet = 'aąbcćdeęfghijklłmnńoóprsśtuwyzźż'
        self.min_length = 2
        self.max_length = 32
        self.words_downloader = WordsDownloader(self.alphabet)
        self.db = Db('words.db')
        self.last_letters = self.db.last_letters()
        self.omit_letters = not self.last_letters is None

    @staticmethod
    def _perm(iterable, fun, repeat=None):
        pool = tuple(iterable)
        number = len(pool)

        repeat = number if repeat is None else repeat
        if repeat > number:
            return

        indices = list(range(number))
        cycles = list(range(number, number - repeat, -1))
        fun(tuple(pool[i] for i in indices[:repeat]))

        while number:
            for i in reversed(range(repeat)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = number - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    fun(tuple(pool[i] for i in indices[:repeat]))
                    break
            else:
                return

    def _on_next_perm(self, tpl):
        letters = ''.join(tpl)

        if self.omit_letters:
            if letters == self.last_letters:
                logging.info('start from previous letters %s: ', self.last_letters)
                self.omit_letters = False
            return

        words = self.words_downloader.get_words(letters)

        if words is None:
            logging.info('no found words for letters: %s', letters)
        else:
            logging.info('found words %s for letters %s', str(words), letters)

        self.db.save_words_and_letters(words, letters)

    def download(self):
        loop = True

        while loop:
            loop = False
            try:
                for i in range(self.min_length, self.max_length + 1):
                    Main._perm(self.alphabet, self._on_next_perm, i)
            except Exception as ex:
                logging.error(ex)
                loop = True

Main().download()
