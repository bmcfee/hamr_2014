#!/usr/bin/env python

import flask
import argparse
import ConfigParser
import sys, os

import searcher

import ujson as json

DEBUG = True

# construct application object
app = flask.Flask(__name__)
app.config.from_object(__name__)

def load_config(server_ini):
    P       = ConfigParser.RawConfigParser()

    P.opionxform    = str
    P.read(server_ini)

    CFG = {}
    for section in P.sections():
        CFG[section] = dict(P.items(section))

    for (k, v) in CFG['server'].iteritems():
        app.config[k] = v
    return CFG

def run(**kwargs):
    app.run(**kwargs)

@app.route('/search/', methods=['GET'], defaults={'query': ''})
@app.route('/search/<path:query>', methods=['GET'])
def search(query):
    return json.encode(searcher.search(query))

@app.route('/')
def index(q):
    '''Top-level web page'''
    return flask.render_template('index.html', query=q)


# Main block
def process_arguments():

    parser = argparse.ArgumentParser(description='Yankomatic web server')

    parser.add_argument(    '-i',
                            '--ini',
                            dest    =   'ini',
                            required=   False,
                            type    =   str,
                            default =   'server.ini',
                            help    =   'Path to server.ini file')

    parser.add_argument(    '-p',
                            '--port',
                            dest    =   'port',
                            required=   False,
                            type    =   int,
                            default =   5000,
                            help    =   'Port')

    parser.add_argument(    '--host',
                            dest    =   'host',
                            required=   False,
                            type    =   str,
                            default =   '0.0.0.0',
                            help    =   'host')

    return vars(parser.parse_args(sys.argv[1:]))
                            
if __name__ == '__main__':
    parameters = process_arguments()

    CFG = load_config(parameters['ini'])

    port = parameters['port']

    if os.environ.get('ENV') == 'production':
        port = int(os.environ.get('PORT'))

    searcher.init(CFG)

    run(host=parameters['host'], port=port, debug=DEBUG)


