import os
import _datetime
import calendar
from datetime import datetime, timedelta
from django.db import connection
from django.db.models import Sum, Count, Avg
from rest_framework.exceptions import ParseError
import nowwapi.settings as settings
from django.core.files.storage import default_storage
from django.core import validators
from django.db import models


def base_swagger_responses(*args, kparams=None):
    """
    Selection of transmitted HTTP responses.
    args: list of int, HTTP responses
    kparams: dict of key is int and to override value
    :return: dict
    """

    base = {
        200: 'OK',
        201: 'Created',
        204: 'No Content',
        401: 'Unauthorized',
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Not Found',
    }
    result = {}
    if args:
        _not_in_base = [x for x in args if x not in base]
        assert not _not_in_base, \
            f'One or more http response are not based on this system.' \
            f'In args: {_not_in_base} not in {list(base.keys())}'
        result = {k: v for k, v in base.items() if k in set(args)}

    if kparams:
        _not_in_base = [x for x in kparams.keys() if x not in base]
        assert not _not_in_base, \
            f'One or more http response are not based on this system.' \
            f'In kparams: {_not_in_base} not in {list(base.keys())}'
        result.update(kparams)

    return result


def calculate_percentage_of_number(x, y):
    result = 0
    if x and y:
        result = x / y * 100
    return float(result).__round__(2)


def calculate_conversion(x, y):
    result = 0
    if x and y:
        result = x / y * 100
    return float(result).__round__(2)


class CustomSerializerClassMixin:

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super().get_serializer_class()


class DateTimeStatistic:

    def __init__(self, entity, expression, field_name, period, aggregate,
                 values_expression, qs=None, is_prev=False):
        """
        Aggregates data by date type: day, week, month, year
        :param entity: django.model.[objects|relation_name]
        :param expression: str
        :param field_name: str, name of the field to be filtered
        :param period: str, (day, week, month, year)
        :param aggregate: str, type of aggregate
        :param values_expression: [str|django expression ORM]
        """
        self.entity = entity
        self.expression = expression
        self.field_name = field_name
        self.period = period
        self.aggregate = aggregate
        self.values_expression = values_expression
        self.qs = qs
        self.is_prev = is_prev

        self.dt_now = datetime.now()
        self.qs = None
        self.annotations = aggregate
        self.labels = None

        if type(self.annotations) == str:
            self.annotations = {
                'count': self.aggregation(self.values_expression)
            }

    @property
    def aggregation(self):
        agg = {
            "count": Count,
            "sum": Sum,
            "avg": Avg
        }.get(self.aggregate)
        assert agg, "aggregation type not entered, please pass " \
                    "one of the types: count, sun, avg"
        return agg

    @staticmethod
    def sort_period(start, finish):
        sort_arr_before = []
        sort_arr_after = []
        for i in range(0, finish):
            a = i + start
            if a >= finish:
                sort_arr_before.append(i - len(sort_arr_after))
            else:
                sort_arr_after.append(a)
        return sort_arr_after + sort_arr_before

    def get_chart_data(self):
        """
        Aggregation types are allocated according to the transferred date types
        :return: dict
        """
        switcher = {
            'day': self.day_chart,
            'week': self.week_chart,
            'month': self.month_chart,
            'year': self.year_chart
        }.get(self.period)

        if not switcher:
            raise Exception('type of date not found')
        result = switcher()
        return result

    def get_data(self):
        """
        Aggregation types are allocated according to the transferred date types
        :return: django.db.models.query.QuerySet
        """
        switcher = {
            'day': self.day,
            'week': self.week,
            'month': self.month,
            'year': self.year
        }.get(self.period)

        if not switcher:
            raise Exception('type of date not found')
        return switcher()

    def day(self):
        today = datetime.today()
        start = datetime(today.year, today.month, today.day, 0, 0)
        finish = datetime.now()
        if self.is_prev:
            start = datetime(today.year, today.month, today.day - 1, 0, 0)
            finish = datetime(today.year, today.month, today.day - 1, 23, 59)

        select = {
            'hour': connection.ops.date_trunc_sql('hour', self.field_name)
        }

        qs = self.execute_expr(start, finish)
        qs = qs.extra(select=select).values('hour') \
            .annotate(**self.annotations) \
            .order_by('hour')
        return qs

    def week(self):
        dt = datetime.now()
        wk = dt.weekday()
        start_date = dt - timedelta(days=wk)
        finish = datetime.now()
        if self.is_prev:
            finish = start_date - timedelta(days=1)
            start_date = finish - timedelta(days=7)

        start = datetime(dt.year, dt.month, start_date.day, 0, 0)

        qs = self.execute_expr(start, finish)
        qs = qs.extra({'day': f"date({self.field_name})"}) \
            .values('day') \
            .annotate(**self.annotations)
        return qs

    def execute_expr(self, start, finish):
        self.qs = self.entity.filter(
            **{f'{self.expression}__range': (start, finish)})
        return self.qs

    def month(self):
        start = datetime(datetime.now().year, datetime.now().month, 1)
        finish = datetime.now()
        if self.is_prev:
            finish = start - timedelta(days=1)
            start = datetime(datetime.now().year, finish.month, 1)
        qs = self.execute_expr(start, finish)
        qs = qs.extra({'day': f"date({self.field_name})"}) \
            .values('day') \
            .annotate(**self.annotations)
        return qs

    def year(self):
        start = datetime(datetime.now().year, 1, 1)
        finish = datetime.now()
        if self.is_prev:
            finish = datetime(datetime.now().year - 1, 12, 31, 23, 59)
            start = datetime(datetime.now().year - 1, 1, 1)

        select = {
            'month': connection.ops.date_trunc_sql('month', self.field_name)
        }
        qs = self.execute_expr(start, finish)
        qs = qs.extra(select=select) \
            .values('month') \
            .annotate(**self.annotations) \
            .order_by('month')
        return qs

    def total_time(self):
        return 1

    def day_chart(self):
        ant = {}
        for k, v in self.annotations.items():
            data = {_datetime.time(i).strftime('%H:%M'): 0 for i in range(0, 24)}
            self.labels = data.keys()
            data.update({
                _datetime.time(i['hour'].hour).strftime('%H:%M'): i['count']
                for i in self.day()
            })
            ant[k] = data
        return ant

    def month_chart(self):
        ant = {}
        for k, v in self.annotations.items():
            start_month_date = datetime(
                datetime.now().year, datetime.now().month, 1
            )
            month_days = calendar.monthrange(
                start_month_date.year, start_month_date.month
            )[1]
            data = {i.__str__(): 0 for i in range(1, month_days + 1)}
            self.labels = data.keys()
            data.update(
                {i['day'].day.__str__(): i[k] for i in self.month()})
            ant[k] = data
        return ant

    def week_chart(self):
        ant = {}
        for k, v in self.annotations.items():
            data = {calendar.day_name[i]: 0 for i in range(0, 6)}
            self.labels = data.keys()
            data.update({
                calendar.day_name[i['day'].weekday()]: i[k] for i in
                self.week()
            })
            ant[k] = data
        return ant

    def year_chart(self):
        ant = {}
        for k, v in self.annotations.items():
            data = {calendar.month_name[i]: 0 for i in range(1, 13)}
            self.labels = data.keys()
            data.update({
                calendar.month_name[i['month'].month]: i[k]
                for i in self.year()
            })
            ant[k] = data
        return ant


def upload_to_backet(file):

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "nowwapi/un-5fd42c0c3503.json"
    backet = settings.GS_BUCKET_NAME

    if not default_storage.exists(file.name):
        file_g = default_storage.open(file.name, 'w')
        file_g.write(file.read())
        file_g.close()

    url = f"https://{backet}.storage.googleapis.com/{file.name}"

    return url


def get_datetime_obj(date_time):
    date_time_format = '%Y-%m-%dT%H:%M:%SZ'
    try:
        if date_time:
            return datetime.strptime(date_time, date_time_format)
        return None
    except ValueError:
        raise ParseError('Invalid date time format')


class GoogleBucketUrlField(models.TextField):
    default_validators = [validators.URLValidator(
        regex="^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
    )]
