#!flask/bin/python

import flask

import memdam.server.web.urls

def run(**kwargs):
    #TODO: figure out how to run this in WSGI mode...
    for key, value in kwargs.items():
        memdam.server.web.app.config[key] = value
    memdam.log = memdam.server.web.urls.app.logger
    memdam.hack_logger(memdam.log)
    memdam.server.web.urls.app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    run()
