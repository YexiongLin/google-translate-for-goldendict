#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Get translate from Google Translate
author: 'YEXIONG LIN'
Created on 2022-10-30 12:55:00
USAGE:
python3 googletranslate.py <target language code> <text to be translated>
python googletranslate.py zh-CN 'hello world!'
"""

import requests
import sys
import urllib.parse
import asyncio
from functools import partial
import re
import argparse
import socket
import socks
from googletranslatetk import Token
import warnings
warnings.filterwarnings("ignore")

class GoogleTranslate(object):
    def __init__(self, args):
        self.http_host = args.host
        self.synonyms_en = args.synonyms
        self.definitions_en = args.definitions
        self.examples_en = args.examples
        self.result_code = 'utf-8' if args.type == 'html' else sys.stdout.encoding
        sys.stdout.reconfigure(encoding=self.result_code) if args.type == 'html' else None
        self.alternative_language = args.alternative
        self.result_type = args.type
        self.target_language = ''
        self.query_string = ''
        self.result = ''

    def get_url(self, tl, qry, tk):
        url = f'https://{self.http_host}/translate_a/single?client=gtx&sl=auto&tl={tl}&hl=en&dt=at&dt=bd&dt=ex&' \
              f'dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=sos&dt=ss&dt=t&ssel=0&tsel=0&kc=1&tk={tk}&q={qry}'
        return url

    def get_synonym(self, resp):
        if resp[1]:
            self.result += '\n=========\n'
            self.result += f'Translations of {self.query_string}\n'
            for x in resp[1]:
                self.result += f'# {x[0][0]}.\n'
                for y in x[2]:
                    self.result += f'{y[0]}: {", ".join(y[1])}\n'

    def get_result(self, resp):
        for x in resp[0]:
            self.result += x[0] if x[0] else ''
        self.result += '\n'

    def get_definitions(self, resp):
        self.result += '\n=========\n'
        self.result += f'Definitions of {self.query_string}\n'
        for x in resp[12]:
            self.result += f'# {x[0] if x[0] else ""}.\n'
            for y in x[1]:
                self.result += f'  - {y[0]}\n'
                self.result += f'    * {y[2]}\n' if len(y) >= 3 else ''

    def get_examples(self, resp):
        self.result += '\n=========\n'
        self.result += f'Examples of {self.query_string}\n'
        for x in resp[13][0]:
            self.result += f'  * {x[0]}\n'

    def get_synonyms_en(self, resp):
        self.result += '\n=========\n'
        self.result += f'Synonyms of {self.query_string}\n'
        for idx, x in enumerate(resp[11]):
            self.result += f'# {x[0]}.\n'
            for y in x[1]:
                self.result += ', '.join(y[0]) + '\n'

    def get_resp(self, url):
        base_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'}
        session = requests.Session()
        session.headers = base_headers
        resp = session.get(url, timeout=5).json()
        return resp

    def result_to_html(self):
        css_text = """\
        <style type="text/css">
        p {white-space: pre-wrap;}
        pos {color: #0000FF;}
        example {color: #008080;}
        gray {color: #606060;}
        </style>"""
        self.result = re.sub(r'(?m)^(#.*)', r'<pos><b>\1</b></pos>', self.result)
        self.result = re.sub(r'(?m)^([*].*)', r'<example>\1</example>', self.result)
        self.result = re.sub(r'(?m)^(.*?of)(.*)', r'<gray>\1</gray>\2', self.result)
        match = re.compile(rf"(?m)^(Translate)(.*)(To)(.*)")
        self.result = match.sub(r'<gray>\1</gray>\2<gray>\3</gray>\4', self.result)
        self.result = f'<html>\n<head>\n{css_text}\n</head>\n<body>\n<p>{self.result}</p>\n</body>\n</html>'

    async def get_translation(self, target_language, query_string, tkk=''):
        self.result = ''
        self.target_language = target_language
        self.query_string = query_string
        tk = Token(tkk).calculate_token(self.query_string)
        if len(self.query_string) > 5000:
            return 'Maximum characters exceeded...'
        parse_query = urllib.parse.quote_plus(self.query_string)
        url = self.get_url(self.target_language, parse_query, tk)
        url_alt = self.get_url(self.alternative_language, parse_query, tk)
        try:
            loop = asyncio.get_running_loop()
            resp = loop.run_in_executor(None, partial(self.get_resp, url))
            resp_alt = loop.run_in_executor(None, partial(self.get_resp, url_alt))
            [resp, resp_alt] = await asyncio.gather(resp, resp_alt)
            if resp[2] == self.target_language:
                self.result += f'Translate {resp[2]} To {self.alternative_language}\n'
                self.get_result(resp)
                self.result += '---------\n'
                self.get_result(resp_alt)
                self.get_synonym(resp_alt)
            else:
                self.result += f'Translate {resp[2]} To {self.target_language}\n{self.query_string}\n---------\n'
                self.get_result(resp)
                self.get_synonym(resp)
            if self.synonyms_en and len(resp) >= 12 and resp[11]:
                self.get_synonyms_en(resp)
            if self.definitions_en and len(resp) >= 13 and resp[12]:
                self.get_definitions(resp)
            if self.examples_en and len(resp) >= 14 and resp[13]:
                self.get_examples(resp)
            if self.result_type == 'html':
                self.result_to_html()
            else:
                self.result = self.result.replace('<b>', '').replace('</b>', '')
            return self.result.encode(self.result_code, 'ignore').decode(self.result_code)
        except requests.exceptions.ReadTimeout:
            return 'ReadTimeout...'
        except requests.exceptions.ProxyError:
            return 'ProxyError...'
        except Exception as e:
            return f'Error: {e}'


def get_args():
    default = '(default: %(default)s)'
    parser = argparse.ArgumentParser()
    parser.add_argument('target', type=str, default='en', help=f'target language, eg: zh-CN, {default}')
    parser.add_argument('query', type=str, default='', help='query string')
    parser.add_argument('-s', dest='host', type=str, default='translate.googleapis.com', help=f'host name {default}')
    parser.add_argument('-p', dest='port', type=int, default=10808, help='socks port (eg: 10808)')
    parser.add_argument('-a', dest='alternative', type=str, default='en', help=f'alternative language {default}')
    parser.add_argument('-r', dest='type', type=str, default='html', help=f'result type {default}')
    parser.add_argument('-k', dest='tkk', type=str, default='', help='tkk')
    parser.add_argument('-m', dest='synonyms', action='store_true', help='show synonyms')
    parser.add_argument('-d', dest='definitions', action='store_true', help='show definitions')
    parser.add_argument('-e', dest='examples', action='store_true', help='show examples')
    parser.add_argument('--proxy', action='store_true', default=False, help='whether use proxy')
    return parser.parse_args()


def main(args=None):
    args = args if args else get_args()
    if args.proxy:
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", args.port)
        socket.socket = socks.socksocket
    g_trans = GoogleTranslate(args)
    trans = asyncio.run(g_trans.get_translation(args.target, args.query, tkk=args.tkk))
    return trans


if __name__ == '__main__':
    print(main())
