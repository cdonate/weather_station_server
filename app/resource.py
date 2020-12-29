# -*- coding: utf-8 -*-
import json
import re

from functools import wraps
from flask import request, g, Response
from flask_restful import Resource
from schema import SchemaError

from app import exceptions, utils, schemas
from app.domain import iot_domain
from app.initialize import web_app


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated = getattr(g, 'authenticated', False)
        if not authenticated:
            return Response('{"result": "Not Authorized"}', 401, content_type='application/json')
        return f(*args, **kwargs)

    return decorated_function


def not_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return Response('{"result": "Method not allowed"}', 405, content_type='application/json')

    return decorated_function


class ResourceBase(Resource):

    def __init__(self):
        self._iot = iot_domain.Iot.get_instance()
        self._payload = None
        self._body = None

    @property
    def iot(self):
        return self._iot

    @staticmethod
    def camel_to_snake(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def snake_to_camel(name):
        result = []
        for index, part in enumerate(name.split('_')):
            if index == 0:
                result.append(part.lower())
            else:
                result.append(part.capitalize())
        return ''.join(result)

    def transform_key(self, data, method):
        if isinstance(data, dict):
            return {method(key): self.transform_key(value, method) for key, value in data.items()}
        if isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    data[index] = {method(key): self.transform_key(value, method) for key, value in item.items()}
        return data

    @property
    def body(self):
        if self._body is None:
            if request.content_type == 'text/csv':
                self._body = utils.parse_csv(request.data)
        return self._body

    @property
    def payload(self):
        if self._payload is None:
            payload = {}

            if request.method != 'GET' and request.json:
                payload.update(self.transform_key(request.json, self.camel_to_snake))
            if request.form:
                payload.update(self.transform_key(request.form, self.camel_to_snake))
            if request.args:
                payload.update(self.transform_key(request.args, self.camel_to_snake))
            self._payload = payload
        return self._payload

    @property
    def payload_with_files(self):
        payload = {}
        if request.json:
            dict = json.loads(request.form['payload'])
            payload.update(self.transform_key(dict, self.camel_to_snake))
        if request.form:
            dict = json.loads(request.form['payload'])
            payload.update(self.transform_key(dict, self.camel_to_snake))
        if request.args:
            dict = json.loads(request.form['payload'])
            payload.update(self.transform_key(dict, self.camel_to_snake))
        payload['files'] = request.files
        return payload

    @property
    def headers(self):
        return request.headers

    @property
    def request(self):
        return {'path': request.path, 'method': request.method, 'endpoint': request.endpoint}

    @property
    def logged_user(self):
        return getattr(g, 'user', None)

    @property
    def files(self):
        return request.files

    def response(self, data_dict):
        return self.transform_key(data_dict, self.snake_to_camel)

    @login_required
    @not_allowed
    def get(self, **kwargs):
        pass

    @login_required
    @not_allowed
    def post(self, **kwargs):
        pass

    @login_required
    @not_allowed
    def put(self, **kwargs):
        pass

    @login_required
    @not_allowed
    def delete(self, **kwargs):
        pass

    def return_bad_parameter(self, **extra):
        result = {'result': 'error', 'error': 'Bad Request', 'exception': 'Bad Request'}
        if extra is not None:
            result.update(extra)
        return result, 400

    def return_unauthorized_error(self):
        return {'result': 'error', 'error': 'Unauthorized', 'exception': 'Unauthorized'}, 401

    def return_forbidden_error(self):
        return {'result': 'error', 'error': 'Forbidden',
                'exception': 'The action you are trying to perform is forbidden'}, 403

    def return_not_found(self):
        return {'result': 'error', 'error': 'Not Found', 'exception': 'The resource requested was not found.'}, 404

    def return_conflict(self):
        return {'result': 'error', 'error': 'Conflict', 'exception': 'The request could not be completed '
                                                                     'due to a conflict with the current state of the '
                                                                     'resource.'}, 409

    def return_unexpected_error(self):
        return {'result': 'error', 'error': 'Internal Server Error', 'exception': 'An unexpected error occurred'}, 500

    def return_ok(self, **extra):
        result = {'result': 'OK'}
        if extra is not None:
            result.update(extra)
        return result


class WeatherResource(ResourceBase):

    # @login_required
    # def get(self, user_lock_id=None):
    #     try:
    #         if user_lock_id is None:
    #             web_app.logger.debug('[START] LocksResource - GET - GET LOCKS FOR USER {}'.format(self.me.id))
    #             user_locks = self.me.get_my_locks()
    # 
    #             web_app.logger.info('[SUCCESS] LocksResource - GET - GET LOCKS FOR USER {}'.format(self.me.id))
    #             return self.response([user_lock.as_dict() for user_lock in user_locks])
    # 
    #         web_app.logger.debug('[START] LocksResource - GET - GET LOCK FOR USER {} BY ID {}'.format(self.me.id, user_lock_id))
    #         user_lock = self.me.get_my_lock_by_id(user_lock_id)
    #         web_app.logger.info('[SUCCESS] LocksResource - GET - GET LOCK FOR USER {} BY ID {}'.format(self.me.id, user_lock_id))
    #         return self.response(user_lock.as_dict())
    # 
    #     except exceptions.NotFound as ex:
    #         return self.return_not_found()
    #     except Exception as ex:
    #         web_app.logger.debug('[ERROR] WeatherResource - GET - Exception {}'.format(str(ex)))
    #         return self.return_unexpected_error()

    def get(self, iot_id=None):
        try:
            web_app.logger.debug('[START] WeatherResource - GET - GET WEATHER DATA FOR ID {}'.format(iot_id))

            if iot_id is None:
                raise exceptions.MissingParameter('iot_id is mandatory for this request')

            weather_data_list = self.iot.get_weather_data(iot_id, self.payload)

            web_app.logger.info('[SUCCESS] WeatherResource - GET - GET WEATHER DATA FOR ID {}'.format(iot_id))
            return self.response([weather_data.as_dict() for weather_data in weather_data_list])
        except SchemaError as se:
            web_app.logger.debug('[ERROR] WeatherResource - GET - SchemaError {}'.format(str(se)))
            return self.return_bad_parameter(message=str(se))
        except Exception as ex:
            web_app.logger.debug('[ERROR] WeatherResource - GET - Exception {}'.format(str(ex)))
            return self.return_unexpected_error()

    def post(self, iot_id):
        try:
            web_app.logger.debug('[START] WeatherResource - POST - SAVE WEATHER DATA FOR ID {}'.format(iot_id))

            schemas.weather_data.validate(self.body)

            self.iot.save_weather_data_in_bulk(iot_id, self.body)
            
            web_app.logger.info('[SUCCESS] WeatherResource - POST - SAVE WEATHER DATA FOR ID {}'.format(iot_id))
            return '', 204
        except SchemaError as se:
            web_app.logger.debug('[ERROR] WeatherResource - POST - SchemaError {}'.format(str(se)))
            return self.return_bad_parameter(message=str(se))
        except Exception as ex:
            web_app.logger.debug('[ERROR] WeatherResource - POST - Exception {}'.format(str(ex)))
            return self.return_unexpected_error()
