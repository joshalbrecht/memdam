#!flask/bin/python

import flask

import memdam.server.web.urls

def run():
    memdam.server.web.urls.app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    run()
