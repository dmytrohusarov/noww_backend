from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg import openapi
from nowwapi.utils import (
    base_swagger_responses, DateTimeStatistic, calculate_percentage_of_number,
    calculate_conversion)
from django.db.models import Case, When, Sum, Avg
from noww.models import Review, CustomerReview, Task, Customer, Worker
from .serializer import (
    ReportCustomerReviewSerializer, ReportTaskSerializer,
    ReportTaskReviewSerializer, ReportCustomerSerializer,
    ReportCustomerTasksSerializer, ReportChartStatisticSerializer,
    ReportHomesStatisticsSerializer
)
from .access import *


class ReviewList(APIView):
    permission_classes = (ReviewListAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="List objects of all reviews / complaints of "
                              "custom",
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportCustomerReviewSerializer(many=True)}
        )
    )
    def get(self, request):
        """
        List of reviews.
        """
        data = CustomerReview.objects.all()
        serializer = ReportCustomerReviewSerializer(data, many=True)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReviewRetrieve(APIView):
    permission_classes = (ReviewRetrieveAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="Object of review / complaints of the customer",
        responses=base_swagger_responses(
            400, 401, 403, 404,
            kparams={200: ReportCustomerReviewSerializer}
        )
    )
    def get(self, request, review_id):
        """
        Retrieve of review.
        """
        review = get_object_or_404(Review, pk=review_id)
        serializer = ReportCustomerReviewSerializer(review.customer_review)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class TaskList(APIView):
    permission_classes = (TaskListAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="List task objects",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: ReportTaskSerializer(many=True)}
        )
    )
    def get(self, request):
        """
        List of tasks.
        """
        data = Task.objects.all()
        serializer = ReportTaskSerializer(data, many=True)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class TaskRetrieve(APIView):
    permission_classes = (TaskListAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="Object of task",
        responses=base_swagger_responses(
            400, 401, 403, 404,
            kparams={200: ReportTaskReviewSerializer()}
        )
    )
    def get(self, request, id):
        """
        Retrieve of task.
        """
        review = get_object_or_404(Task, pk=id)
        serializer = ReportTaskReviewSerializer(review)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.errors, 403)


class CustomerRetrieve(APIView):
    permission_classes = (CustomerRetrieveAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="Object of customer",
        responses=base_swagger_responses(
            400, 401, 403, 404,
            kparams={200: ReportCustomerSerializer()}
        )
    )
    def get(self, request, id):
        """
        Retrieve of task.
        """
        customer = get_object_or_404(Customer, pk=id)
        serializer = ReportCustomerSerializer(customer)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.errors, 403)


class CustomerTasks(APIView):
    permission_classes = (CustomerTasksAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports'],
        operation_description="List of task objects of a specific customer",
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportCustomerTasksSerializer(many=True)}
        )
    )
    def get(self, request, customer_id):
        """
        List of tasks.
        """
        customer = get_object_or_404(Customer, pk=customer_id)
        tasks = customer.tasks
        data = {'customer': customer, 'tasks': tasks.all()}
        serializer = ReportCustomerTasksSerializer(data)
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportWorkersChart(APIView):
    permission_classes = (ReportWorkersChartAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="The method returns an aggregated data object, "
                              "Worker entities by period.",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            ),
            openapi.Parameter(
                'types',
                openapi.IN_QUERY,
                description="Type of Aggregation Schedules Required "
                            "(registered, profit, avg)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING)
            ),
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportChartStatisticSerializer()}
        )
    )
    def get(self, request):
        period = request.GET.get('period', 'day')
        types = request.GET.get('types', 'registered,profit,avg')
        types = types.split(',')
        labels = None
        datasets = []
        type_ = 'profit'
        if type_ in types:
            qs = DateTimeStatistic(
                Worker.objects, 'tasks__created_at', 'created_at', period,
                'sum', 'tasks__delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#3bafdac7', 'borderColor': 'info',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'avg'
        if type_ in types:
            qs = DateTimeStatistic(
                Worker.objects, 'tasks__created_at', 'created_at', period,
                'avg', 'tasks__delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#ffc1079c', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'registered'
        if type_ in types:
            qs = DateTimeStatistic(
                Worker.objects, 'user__date_joined', 'date_joined', period,
                'count', 'id'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#20C997', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        if not labels:
            return Response(
                {"type": "not one of the passed types is acceptable {0}".
                    format(types)}, 403
            )
        serializer = ReportChartStatisticSerializer(
            {'labels': list(labels), 'datasets': datasets}
        )
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportCustomersChart(APIView):
    permission_classes = [ReportCustomersChartAccessPolicy, ]

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="The method displays aggregated data for "
                              "periods.",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            ),
            openapi.Parameter(
                'types',
                openapi.IN_QUERY,
                description="Type of Aggregation Schedules Required "
                            "(registered, profit, avg)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
            ),
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportChartStatisticSerializer()}
        )
    )
    def get(self, request):
        period = request.GET.get('period', 'day')
        types = request.GET.get('types', 'registered,profit,avg')
        types = types.split(',')
        labels = None
        datasets = []
        type_ = 'profit'
        if type_ in types:
            qs = DateTimeStatistic(
                Customer.objects, 'tasks__created_at', 'created_at', period,
                'sum', 'tasks__delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#ffc1079c', 'borderColor': 'info',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'avg'
        if type_ in types:
            qs = DateTimeStatistic(
                Customer.objects, 'tasks__created_at', 'created_at', period,
                'avg', 'tasks__delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#3bafdac7', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'registered'
        if type_ in types:
            qs = DateTimeStatistic(
                Customer.objects, 'user__date_joined', 'date_joined', period,
                'count', 'id'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#20C997', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        if not labels:
            return Response(
                {"type": "not one of the passed types is acceptable {0}".
                    format(types)}, 403
            )
        serializer = ReportChartStatisticSerializer(
            {'labels': labels, 'datasets': datasets}
        )
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportTasksChart(APIView):
    permission_classes = (ReportTasksChartAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="The method returns an aggregated data object, "
                              "Task entities by period.",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            ),
            openapi.Parameter(
                'types',
                openapi.IN_QUERY,
                description="Type of Aggregation Schedules Required "
                            "(ready, all)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
            ),
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportChartStatisticSerializer(many=True)}
        )
    )
    def get(self, request):
        period = request.GET.get('period', 'day')
        types = request.GET.get('types', 'ready,all')
        types = types.split(',')
        labels = None
        datasets = []

        type_ = 'ready'
        if type_ in types:
            values_expression = Case(
                When(status=type_.upper(), then='status')
            )
            qs = DateTimeStatistic(
                Task.objects, 'created_at', 'created_at', period, 'count',
                values_expression
                )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#3bafdac7', 'borderColor': 'info',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'all'
        if type_ in types:
            qs = DateTimeStatistic(
                Task.objects, 'created_at', 'created_at', period, 'count', 'id'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#ffc1079c', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        if not labels:
            return Response(
                {"type": "not one of the passed types is acceptable {0}".
                    format(types)}, 403
            )
        serializer = ReportChartStatisticSerializer(
            {'labels': labels, 'datasets': datasets}
        )
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportReviewsChart(APIView):
    permission_classes = (ReportReviewsChartAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="The method returns an aggregated data object, "
                              "Review entities by period.",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            ),
            openapi.Parameter(
                'types',
                openapi.IN_QUERY,
                description="Type of Aggregation Schedules Required "
                            "(count)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
            ),
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportChartStatisticSerializer(many=True)}
        )
    )
    def get(self, request):
        period = request.GET.get('period', 'day')
        types = request.GET.get('types', 'count')
        types = types.split(',')
        labels = None
        datasets = []

        type_ = 'count'
        if type_ in types:
            qs = DateTimeStatistic(
                Review.objects, 'created_at', 'created_at', period, 'count',
                'id'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#ffc1079c', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        if not labels:
            return Response(
                {"type": "No such type {0}".format(types)}, 403
            )

        serializer = ReportChartStatisticSerializer(
            {'labels': labels, 'datasets': datasets}
        )
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportWorkerChart(APIView):
    permission_classes = (ReportWorkerChartAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="The method returns an aggregated data object, "
                              "Worker object by period.",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            ),
            openapi.Parameter(
                'types',
                openapi.IN_QUERY,
                description="Type of Aggregation Schedules Required "
                            "(profit, avg)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
            ),
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportChartStatisticSerializer(many=True)}
        )
    )
    def get(self, request, worker_id):
        worker = get_object_or_404(Worker, id=worker_id)
        period = request.GET.get('period', 'day')
        types = request.GET.get('types', 'profit,avg')
        types = types.split(',')
        labels = None
        datasets = []

        type_ = 'profit'
        if type_ in types:
            qs = DateTimeStatistic(
                worker.tasks, 'created_at', 'created_at', period, 'sum',
                'delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#ffc1079c', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        type_ = 'avg'
        if type_ in types:
            qs = DateTimeStatistic(
                worker.tasks, 'created_at', 'created_at', period, 'avg',
                'delivery_cost'
            )
            result = qs.get_chart_data()
            # TODO: refactoring, outgoing to templates
            dataset = {
                'label': type_, 'data': result['count'].values(),
                'backgroundColor': '#3bafdac7', 'borderColor': 'danger',
                'borderWidth': 1
            }
            datasets.append(dataset)
            labels = qs.labels

        if not labels:
            return Response(
                {"type": "No such type {0}".format(types)}, 403
            )

        serializer = ReportChartStatisticSerializer(
            {'labels': labels, 'datasets': datasets}
        )
        if serializer.data:
            return Response(serializer.data, 200)
        return Response(serializer.data, 204)


class ReportHomeStatistics(APIView):
    permission_classes = (ReportHomeStatisticsChartAccessPolicy,)

    @swagger_auto_schema(
        tags=['Reports Chart'],
        operation_description="",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Type of Period (day, week, month, year)",
                type=openapi.TYPE_STRING,
                default='day'
            )
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: ReportHomesStatisticsSerializer(many=True)}
        )
    )
    def get(self, request):
        period = request.GET.get('period', 'year')

        # ---==== WORKERS ====--- #
        workers_statistics = DateTimeStatistic(
            Worker.objects, 'user__date_joined', 'date_joined', period,
            'count', 'id'
        )
        workers_statistics.get_data()
        current_count = workers_statistics.qs.count()
        chart_data = workers_statistics.get_chart_data()
        qs_table = workers_statistics.qs.values('user__first_name').annotate(
            profit=Sum('tasks__delivery_cost')
        ).order_by('profit')[:5]
        qs_table = sorted(qs_table, key=lambda t: t['profit'] is not None)

        workers_statistics.is_prev = True
        prev_count = workers_statistics.qs.count()
        ratio = calculate_percentage_of_number(prev_count, current_count)

        table = []
        qs_table.reverse()
        for x in qs_table:
            table.append([{'key': k, 'value': v} for k, v in x.items()])

        # TODO: refactoring, outgoing to templates
        workers_chart = {
            'label': 'Workers', 'data': chart_data['count'].values(),
            'backgroundColor': '#3BAFDA', 'borderColor': 'danger',
            'borderWidth': 1
        }
        worker = {
            "name": 'Workers',
            "data": {
                "values": {"count": current_count},
                "ratio": ratio,
                'datasets': [workers_chart],
                "table": table
            }
        }

        # # ---==== CUSTOMERS ====--- #
        customers_statistics = DateTimeStatistic(
            Customer.objects, 'user__date_joined', 'date_joined', period,
            'count', 'id'
        )
        customers_statistics.get_data()
        current_count = customers_statistics.qs.count()
        chart_data = customers_statistics.get_chart_data()
        qs_table = customers_statistics.qs.values('user__first_name').annotate(
            profit=Sum('tasks__delivery_cost')
        ).order_by('profit')[:5]
        qs_table = sorted(qs_table, key=lambda t: t['profit'] is not None)

        customers_statistics.is_prev = True
        prev_count = customers_statistics.qs.count()
        ratio = calculate_percentage_of_number(prev_count, current_count)

        table = []
        qs_table.reverse()
        for x in qs_table:
            table.append([{'key': k, 'value': v} for k, v in x.items()])
        # TODO: refactoring, outgoing to templates
        customer_chart = {
            'label': 'Customers', 'data': chart_data['count'].values(),
            'backgroundColor': '#DA4453', 'borderColor': 'danger',
            'borderWidth': 1
        }
        customer = {
            "name": 'Customers',
            "data": {
                "values": {"count": current_count},
                "ratio": ratio,
                'datasets': [customer_chart],
                "table": table
            }
        }

        # # ---==== CONVERSION ====--- #
        conversion_statistics = DateTimeStatistic(
            Task.objects, 'created_at', 'created_at', period,
            'sum', 'delivery_cost'
        )
        conversion_statistics.get_data()
        current_count = conversion_statistics.qs.count()
        ready_count = conversion_statistics.qs.filter(status='READY').count()
        conversion = calculate_conversion(ready_count, current_count)
        chart_data = conversion_statistics.get_chart_data()
        qs_table = conversion_statistics.qs.values('worker').annotate(
            total=Sum('delivery_cost')).order_by('total')[:5]
        qs_table = sorted(qs_table, key=lambda t: t['total'] is not None)

        conversion_statistics.is_prev = True
        prev_count = conversion_statistics.qs.count()
        ratio = calculate_percentage_of_number(prev_count, current_count)

        table = []
        # qs_table.reverse()
        for x in qs_table:
            table.append([{'key': k, 'value': v} for k, v in x.items()])

        # TODO: refactoring, outgoing to templates
        conversion_chart = {
            'label': 'Conversion', 'data': chart_data['count'].values(),
            'backgroundColor': '#20C997', 'borderColor': 'danger',
            'borderWidth': 1
        }
        conversion = {
            "name": 'Conversion',
            "data": {
                "values": {"count": conversion},
                "ratio": ratio,
                'datasets': [conversion_chart],
                "table": table
            }
        }

        # # ---==== TOTAL, AVG ====--- #
        profit = DateTimeStatistic(
            Task.objects, 'created_at', 'created_at', period,
            {'avg': Avg('delivery_cost'), 'total': Sum('delivery_cost')},
            'delivery_cost'
        )
        data = profit.get_data()
        total = data[0]['total'] if data else 0
        avg = data[0]['avg'] if data else 0

        chart_data = profit.get_chart_data()
        qs_table = profit.qs.values('worker')\
            .annotate(total=Sum('delivery_cost'), avg=Avg('delivery_cost'))\
            .order_by('total')
        qs_table = sorted(qs_table, key=lambda t: t['total'] is not None)

        profit.is_prev = True
        aggr_prev = profit.qs.filter(status='READY').values('worker')\
            .annotate(total=Sum('delivery_cost')).first()
        prev_total = aggr_prev['total'] if aggr_prev else 0
        ratio = calculate_percentage_of_number(prev_total, total) \
            if prev_total and data else 0

        table = []
        qs_table.reverse()
        for x in qs_table:
            table.append([{'key': k, 'value': v} for k, v in x.items()])

        # TODO: refactoring, outgoing to templates
        conversion_chart_avg = {
            'label': 'AVG', 'data': chart_data['avg'].values(),
            'backgroundColor': '#CCCCCC', 'borderColor': 'danger',
            'borderWidth': 1
        }
        conversion_chart_total = {
            'label': 'Profit', 'data': chart_data['total'].values(),
            'backgroundColor': '#F6BB42', 'borderColor': 'danger',
            'borderWidth': 1
        }
        avg_sum = {
            "name": 'Profit',
            "data": {
                "values": {"total": total, "avg": avg},
                "ratio": ratio,
                'datasets': [conversion_chart_total, conversion_chart_avg],
                "table": table
            }
        }

        serializer = ReportHomesStatisticsSerializer(
            {'labels': profit.labels, 'workers': worker,
             'customers': customer, 'conversion': conversion, 'profit': avg_sum}
        )
        return Response(serializer.data, 200)
