#!/usr/bin/env python3

import json
from pprint import pprint
from urllib.parse import urljoin

import requests

URL = 'https://api.noopschallenge.com/fizzbot/'
DB_FILE = 'fizzbot.db'


class Answerer:

    db = {}
    index = None

    def url(self):
        if not self.index:
            return URL

        return urljoin(urljoin(URL, 'questions/'), self.index)

    def get_question(self):
        if self.index in self.db:
            return

        r = requests.get(self.url())
        q = r.json()

        self.db[self.index] = {'question': q}

        pprint(q)

    def answer(self):
        if not self.index:
            self.index = '1'  # no answering for the introduction
            return

        if 'answer' in self.db[self.index] and self.db[self.index].get('ack', {}).get('result') == 'correct':
            answer = self.db[self.index]['answer']
        else:
            answer = input('Answer: ')
            self.db[self.index]['answer'] = answer

        r = requests.post(self.url(), json={'answer': answer})
        ack = r.json()

        self.db[self.index]['ack'] = ack
        pprint(ack)

        assert ack['result'] == 'correct'
        self.save()

        self.index = ack['nextQuestion'].split('/')[-1]

    def load(self):
        try:
            with open(DB_FILE, 'r') as f:
                self.db = json.loads(f.read())
        except Exception:
            print('Could not load db.')

    def save(self):
        with open(DB_FILE, 'w') as f:
            f.write(json.dumps(self.db))


def main():
    a = Answerer()
    a.load()

    for _ in range(10):
        a.get_question()
        a.answer()


if __name__ == '__main__':
    main()
