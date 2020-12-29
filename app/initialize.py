# -*- coding: utf-8 -*-

import os
import logging

from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy

from app import database
from app import config as config_module, api
from app.domain import services

config = config_module.get_config()

web_app = Flask(__name__)
web_app.config.from_object(config)
database.AppRepository.db = SQLAlchemy(web_app)

api.create_api(web_app)

gunicorn_logger = logging.getLogger('gunicorn.error')
web_app.logger.handlers = gunicorn_logger.handlers
web_app.logger.setLevel(gunicorn_logger.level)


# TODO: Imagino que outros micro serviços também precisarão. Poderiamos jogar isso num pypi privado nosso
# mas por hora imagino que seria bacana tomar o cuidado de fazer isso de maneira beeeem isolada, para futuramente
# ser um ctrl+c ctrl+v

@web_app.before_request
def before_request():
    try:
        token = get_token()
        if token is not None:
            api_request = services.UserApiService.get_user_data(token)

            if api_request.is_success:
                setattr(g, 'user', api_request.result)
                setattr(g, 'authenticated', True)
                setattr(g, 'source', request.user_agent)
                web_app.logger.info('[INFO] initialize.py - login validated - {}'.format(str(api_request.result)))
            else:
                invalidate_user_login()
                web_app.logger.warn('[WARN] initialize.py - before_request - Invalid credentials: {}'.format(str(token)))

        else:
            invalidate_user_login()
            web_app.logger.warn('[WARN] initialize.py - before_request - Empty token')

    except Exception as ex:
        invalidate_user_login()
        web_app.logger.error('[ERROR] initialize.py - before_request - {}'.format(str(ex)))
        return {'result': 'error', 'error': ex, 'exception': 'An unexpected error occurred'}, 500


def invalidate_user_login():
    setattr(g, 'user', None)
    setattr(g, 'authenticated', False)


@web_app.after_request
def add_cache_header(response):
    """
    Add response headers for Cache Control
    """
    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@web_app.after_request
def add_token_header(response):
    # TODO: ver se vai precisar de alguma coisa aqui
    return response


def get_token():
    token = request.cookies.get('elsysUserToken')
    if token is None:
        token = request.headers.get('Authorization')
        if token is not None:
            try:
                token = token.split(' ')[1]
            except IndexError:
                return None
    return token

# If you want to serve your files using python
# Only use it for development
# if config.ENVIROMENT == 'development':
#     def index():
#         return send_from_directory(os.environ.get('WWW_FOLDER', ''), 'index.html')
#
#     def www(custom_path):
#         return send_from_directory(os.environ.get('WWW_FOLDER', ''), custom_path)
#
#     web_app.add_url_rule('/', 'index', index)
#     web_app.add_url_rule('/<path:custom_path>', 'www', www)


def run():
    """
    Run the flask app in a development enviroment
    """
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
