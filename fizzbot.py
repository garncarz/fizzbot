#!/usr/bin/env python3

import json
from pprint import pprint
import traceback
from urllib.parse import urljoin

import requests

URL = 'https://api.noopschallenge.com/fizzbot/'
DB_FILE = 'fizzbot.db'

MOCK_QUESTIONS = {
    1: {},
    3: {
        'message': 'FizzBuzz',
        'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        'rules': [{'number': 3, 'response': 'Fizz'},
                  {'number': 5, 'response': 'Buzz'}],
    },
    6: {
        'message': 'BeepBoop',
        'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'rules': [{'number': 2, 'response': 'Beep'},
                  {'number': 5, 'response': 'Boop'}],
    },
}


class Answerer:

    db = {}
    index = None
    question_nr = 0
    finished = False

    def __init__(self):
        self.session = requests.Session()

    @property
    def url(self):
        if not self.index:
            return URL

        return urljoin(urljoin(URL, 'questions/'), self.index)

    @property
    def item(self):
        return self.db[self.index]

    @property
    def q(self):
        return self.item['question']

    @property
    def qm(self):
        return self.q['message']

    def predict_question(self):
        if self.question_nr in MOCK_QUESTIONS.keys():
            print('... using a mocked question.')
            self.db[self.index] = {'question': MOCK_QUESTIONS[self.question_nr]}
            return True

    def get_question(self):
        self.question_nr += 1
        print(f'Question nr.: {self.question_nr}')

        if self.index not in self.db:
            if self.predict_question():
                return

            print('Will download a new question...')
            r = self.session.get(self.url)
            q = r.json()
            self.db[self.index] = {'question': q}

        pprint(self.q)

    def answer(self):
        if not self.index:
            self.index = '1'  # no answering for the introduction
            return

        if 'answer' in self.item and self.item.get('ack', {}).get('result') in ['correct', 'interview complete']:
            answer = self.item['answer']
        else:
            for fn in filter(lambda attr: attr.startswith('solve_'), dir(self)):
                try:
                    answer = getattr(self, fn)()
                    if answer:
                        print(f'My answer: {answer}')
                        break
                except Exception:
                    print(f'Automated answering {fn} failed.')
                    traceback.print_exc()

            else:
                answer = input('Answer: ')

            self.item['answer'] = answer

        r = self.session.post(self.url, json={'answer': answer})
        ack = r.json()

        self.item['ack'] = ack
        pprint(ack)

        assert ack['result'] in ['correct', 'interview complete']
        self.save()

        if ack['result'] == 'interview complete':
            self.finished = True
            return

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

    def solve_dividing(self):
        if not (
            ('Fizz' in self.qm and 'Buzz' in self.qm)
            or ('Beep' in self.qm and 'Boop' in self.qm)
            or self.qm == 'Here are a few more numbers. The same rules apply.'
            or 'This time there are three rules. Can you figure out what to do?' in self.qm
        ):
            return

        resp = ''

        for n in self.q['numbers']:
            match = False

            for r in self.q['rules']:
                if n % r['number'] == 0:
                    resp += r['response']
                    match = True

            if not match:
                resp += str(n)

            resp += ' '

        return resp[:-1]


def main():
    a = Answerer()
    a.load()

    while not a.finished:
        a.get_question()
        a.answer()


if __name__ == '__main__':
    main()
