# -*- coding: utf-8 -*-
from app.domain import services


class Iot(object):
    @classmethod
    def save_weather_data_in_bulk(cls, iot_id, weather_data):
        services.WeatherService.save_weather_data_in_bulk(iot_id, weather_data)

    @classmethod
    def get_weather_data(cls, iot_id, query_data):
        return services.WeatherService.get_weather_data(iot_id, query_data)

    @classmethod
    def get_instance(cls):
        return cls()
