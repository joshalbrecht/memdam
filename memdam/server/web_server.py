#!flask/bin/python

import flask

import memdam.server.web.urls

if __name__ == '__main__':
    memdam.server.web.urls.app.run(debug=True, use_reloader=False)
