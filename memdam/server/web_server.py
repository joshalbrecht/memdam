#!flask/bin/python

import flask

import memdam.server.web.urls

def run():
    #TODO: figure out how to run this in WSGI mode...
    memdam.log = memdam.server.web.urls.app.logger
    memdam.hack_logger(memdam.log)
    memdam.server.web.urls.app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    run()
