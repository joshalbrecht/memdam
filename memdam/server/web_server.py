#!flask/bin/python

import flask

import memdam.server.web

#TODO: refactor auth stuff
#TODO: unit tests of each
#TODO: integration tests of server
#TODO: client
#TODO: unit tests of client
#TODO: integration tests of client and server
#TODO: use rest client instead of email
#TODO: ssl: http://flask.pocoo.org/snippets/111/
#TODO: deployment (joshalbrecht.chronographr.com)

if __name__ == '__main__':
    memdam.server.web.app.run(debug = True)
