from rest_framework import serializers
from noww.models import (
    Review, User, CustomerReview, Customer, Place, Worker, Task, TaskItem
)
from noww.serializers import (
    TaskSerializer, ServiceSerializer, PlaceSerializer, ProductSerializer
)


class ReportUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "id", "last_login", "first_name", "email", "first_name",
            "last_name", "phone_number"
        )


class ReportWorkerSerializer(serializers.ModelSerializer):
    user = ReportUserSerializer()

    class Meta:
        model = Worker
        fields = "__all__"


class ReportPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ("id", "created_at", "title", "description")


class ReportCustomerSerializer(serializers.ModelSerializer):
    user = ReportUserSerializer(many=False)

    class Meta:
        model = Customer
        fields = "__all__"


class ReportReviewSerializer(serializers.ModelSerializer):
    customer = ReportCustomerSerializer(many=False)

    class Meta:
        model = Review
        fields = "__all__"
        # fields = ('id', 'first_name', 'last_name')


class ReportCustomerReviewSerializer(serializers.ModelSerializer):
    review = ReportReviewSerializer(many=False)
    place = ReportPlaceSerializer(many=False)
    worker = ReportWorkerSerializer(many=False)

    class Meta:
        model = CustomerReview
        fields = "__all__"


class ReportTaskItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False)

    class Meta:
        model = TaskItem
        fields = "__all__"
        # fields = ('product', )


class AddressSerializer():
    pass


class ReportTaskSerializer(TaskSerializer):
    service = ServiceSerializer()
    customer = ReportCustomerSerializer()
    worker = ReportWorkerSerializer()
    place = PlaceSerializer()

    class Meta:
        model = Task
        fields = "__all__"
        # fields = ("task_address", )


class ReportTaskReviewSerializer(ReportTaskSerializer):
    service = ServiceSerializer()
    customer = ReportCustomerSerializer()
    worker = ReportWorkerSerializer()
    place = PlaceSerializer()
    items = ReportTaskItemSerializer(
        source='tasks', many=True, read_only=True
    )

    class Meta:
        model = Task
        fields = "__all__"


class ReportCustomerTasksSerializer(serializers.Serializer):
    customer = ReportCustomerSerializer()
    tasks = ReportTaskSerializer(many=True)


class ReportDataSetItemStatisticSerializer(serializers.Serializer):
    label = serializers.CharField()
    data = serializers.ListField(child=serializers.IntegerField())
    backgroundColor = serializers.CharField()
    borderColor = serializers.CharField()
    borderWidth = serializers.CharField()


class ReportMiniTable(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()  # TODO: change in process


class ReportChartStatisticSerializer(serializers.Serializer):
    datasets = ReportDataSetItemStatisticSerializer(many=True)
    labels = serializers.ListField(child=serializers.CharField())


class ReportDataByPeriodSerializer(serializers.Serializer):
    values = serializers.DictField()
    ratio = serializers.FloatField()
    datasets = serializers.ListField()
    table = serializers.ListField(child=ReportMiniTable(many=True))


class DataSetHomeWidgetSerializer(serializers.Serializer):
    name = serializers.CharField()
    data = ReportDataByPeriodSerializer()


class ReportHomesStatisticsSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    workers = DataSetHomeWidgetSerializer()
    customers = DataSetHomeWidgetSerializer()
    conversion = DataSetHomeWidgetSerializer()
    profit = DataSetHomeWidgetSerializer()
#
#
# class TaskByCustomerSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Task
