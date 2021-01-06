# -*- coding: utf-8 -*-
import datetime

from app import models


class Weather:
    repository = models.WeatherStation

    @classmethod
    def prepare_db_dict_list(cls, iot_id, weather_data):
        for index,data in enumerate(weather_data):
            unformated_date = datetime.datetime.now() - datetime.timedelta(minutes=((len(weather_data)-int(index))*5.0))
            formated_date = unformated_date.strftime("%Y-%m-%d %H:%M:%S")
            data['iot_id'] = iot_id
            data['datetime'] = formated_date
        return weather_data

    @classmethod
    def save_data_in_bulk(cls, iot_id, weather_data):
        db_list_dict = cls.prepare_db_dict_list(iot_id, weather_data)

        for db_dict in db_list_dict:
            db_instance = cls.repository.create_from_json_without_commit(db_dict)
            cls.repository.add_batch(db_instance)
        cls.repository.commit_batch()

    @classmethod
    def get_data(cls, iot_id, query_data):
        weather_data_list = []
        weather_data_list_db_instance = cls.repository.filter_by_datetime(query_data, iot_id)

        for weather_data_db_instance in weather_data_list_db_instance:
            weather_data_list.append(cls.create_from_db_instance(weather_data_db_instance))

        return weather_data_list

    @classmethod
    def create_from_db_instance(cls, db_instance):
        return cls(db_instance)

    def __init__(self, db_instance):
        self.id = db_instance.id
        self._db_instance = db_instance

    @property
    def iot_id(self):
        return self._db_instance.iot_id

    @property
    def temperature(self):
        return self._db_instance.temperature

    @property
    def humidity(self):
        return self._db_instance.humidity

    @property
    def pressure(self):
        return self._db_instance.pressure

    @property
    def rainfall(self):
        return self._db_instance.rainfall

    @property
    def datetime(self):
        return self._db_instance.datetime
    
    def as_dict(self):
        return {
            'id': self.id,
            'iot_id': self.iot_id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'rainfall': self.rainfall,
            'datetime': str(self.datetime)
        }
