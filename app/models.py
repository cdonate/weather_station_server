# -*- coding: utf-8 -*-
import unicodedata
import datetime
from sqlalchemy import and_

from app import database
from app import config as config_module, exceptions

db = database.AppRepository.db

config = config_module.get_config()


class UtilsModel(object):
    class AlreadyExist(Exception):
        pass

    class NotExist(Exception):
        pass

    class RepositoryError(Exception):
        pass

    @classmethod
    def get_all_ids_in(cls, items_id):
        return db.session.query(cls).filter(cls.id.in_(items_id)).all()

    @classmethod
    def one_or_none(cls, **kwargs):
        return cls.filter(**kwargs).one_or_none()

    @classmethod
    def filter(cls, *args):
        return cls.query.filter(*args).all()

    @classmethod
    def get_list(cls, *args, **kwargs):
        return cls.query.filter_by()

    @classmethod
    def get_item(cls, item_id):
        item = cls.query.get(item_id)
        if not item:
            raise cls.NotExist
        else:
            return item

    @classmethod
    def slugify(cls, value):
        slug = unicodedata.normalize('NFKD', value)
        slug = slug.replace(' ', '-')
        slug = slug.encode('ascii', 'ignore').lower()
        return slug

    @classmethod
    def close_session(cls):
        db.session.remove()

    def delete_db(self):
        db.session.delete(self)
        db.session.commit()

    def save_db(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        else:
            db.session.flush()

    @staticmethod
    def commit_session():
        db.session.commit()

    @classmethod
    def add_batch(cls, instance):
        db.session.add(instance)

    @classmethod
    def commit_batch(cls):
        db.session.commit()
        db.session.flush()

    @classmethod
    def create_from_json(cls, json_data):
        try:
            instance = cls()
            instance.set_values(json_data)
            instance.save_db()
            return instance
        except Exception as ex:
            if 'UniqueViolation' in str(ex):
                raise exceptions.AlreadyExists(str(ex))
            if 'InvalidDatetimeFormat' in str(ex):
                raise exceptions.BadParameter('Invalid datetime format')
            raise cls.RepositoryError(str(ex))

    @classmethod
    def create_from_json_without_commit(cls, json_data):
        try:
            instance = cls()
            instance.set_values(json_data)
            instance.save_db(commit=False)
            return instance
        except Exception as ex:
            raise cls.RepositoryError(str(ex))

    @classmethod
    def update_from_json(cls, item_id, json_data):
        try:
            instance = cls.get_item(item_id)
            instance.set_values(json_data)
            instance.save_db()
            return instance
        except db.IntegrityError as ex:
            raise cls.RepositoryError(ex.message)

    @classmethod
    def save_in_batch(cls, piece_values_to_save):
        db.session.bulk_save_objects(piece_values_to_save)
        db.session.commit()

    def set_values(self, json_data):
        for key, value in json_data.items():
            setattr(self, key, json_data.get(key, getattr(self, key)))

    @classmethod
    def roll_back_session(cls):
        db.session.rollback()


class WeatherStation(db.Model, UtilsModel):
    __tablename__ = 'weather_station'
    id = db.Column(db.Integer, primary_key=True)
    iot_id = db.Column(db.Integer, nullable=False)

    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    pressure = db.Column(db.Float, nullable=True)
    rainfall = db.Column(db.Integer, nullable=True)

    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    @classmethod
    def filter_by_datetime(cls, query_data, iot_id):
        terms = [cls.iot_id == iot_id]
        for key in query_data:
            try:
                if key == 'start_date':
                    terms.append(cls.datetime >= datetime.datetime.fromisoformat(query_data[key]))
                elif key == 'end_date':
                    terms.append(cls.datetime <= datetime.datetime.fromisoformat(query_data[key]))
            except ValueError:
                continue
        return cls.filter(and_(*terms))
