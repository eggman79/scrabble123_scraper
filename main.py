#!/usr/bin/python3

import os
import os.path
import re
import urllib.parse

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
        return Request(url, headers=self.request_header)

    def _get_html_for_letters(self, letters):
        return urlopen(self._make_request(letters)).read()

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

class WordsSaver:
    def __init__(self, words_file_name, letters_file_name):
        self.words_file_name = words_file_name
        self.letters_file_name = letters_file_name

    def add_words_for_letters(self, words, letters):
        if not words is None:
            words_file = open(self.words_file_name, 'a')
            for word in words:
                words_file.write(word + '\n')
            words_file.close()

        if os.path.exists(self.letters_file_name):
            os.remove(self.letters_file_name)

        letters_file = open(self.letters_file_name, 'w')
        letters_file.write(letters)
        letters_file.close()

    def get_last_letters(self):
        if not os.path.exists(self.letters_file_name):
            return None
        letters_file = open(self.letters_file_name, 'r')
        letters = letters_file.readline()
        letters_file.close()
        return letters

class Main:
    def __init__(self):
        self.alphabet = 'aąbcćdeęfghijklłmnńoóprsśtuwyzźż'
        self.min_length = 2
        self.max_length = 32
        self.words_saver = WordsSaver('words.txt', 'letters.txt')
        self.last_letters = self.words_saver.get_last_letters()
        self.omit_letters = not self.last_letters is None
        self.words_downloader = WordsDownloader(self.alphabet)

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
                self.omit_letters = False
            return

        words = self.words_downloader.get_words(letters)
        if words is None:
            print(letters)
        else:
            print(str(words) + ':' + letters)
        self.words_saver.add_words_for_letters(words, letters)

    def download(self):
        loop = True

        while loop:
            loop = False
            try:
                for i in range(self.min_length, self.max_length + 1):
                    Main._perm(self.alphabet, self._on_next_perm, i)
            except Exception as ex:
                loop = True

Main().download()
