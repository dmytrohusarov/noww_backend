import json
from rest_framework import viewsets
from rest_framework.decorators import action
from Common import configs
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from .serializers import *
from rest_framework.generics import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from nowwapi.utils import CustomSerializerClassMixin
from .models import *
from .access import *
from nowwapi.utils import base_swagger_responses, upload_to_backet, get_datetime_obj


class WorkersViewSet(viewsets.ModelViewSet):

    queryset = Worker.objects.all()
    model = Worker
    serializer_class = WorkerSerializer
    permission_classes = (WorkerAccessPolicy,)

    @swagger_auto_schema(
        tags=['Workers'],

        operation_description="Method to get a list of workers"
                              " within your access",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: WorkerSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of workers.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_description="Creating a new user in the system as worker",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new worker.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_description="Method to get worker object. This user method "
                              "is installed in the system as the order "
                              "executor of the service.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: WorkerSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve worker.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_description="Updating a worker object in the system",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update worker.
        """
        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_description="Updating individual worker "
                              "fields in the system",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial worker update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_description="Removing a worker record "
                              "from the system",
        responses=base_swagger_responses(204, 401, 403, 404)
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Delete worker.
        """
        return super().destroy(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Workers'],
        operation_id="workers_approve_partial_update",
        operation_description="Worker approval",
        request_body=WorkerApproveSerializer,
        responses=base_swagger_responses(200, 401, 403, 404)
    )
    @action(methods=["PATCH"], detail=True)
    def approve(self, request, pk, *args, **kwargs):
        worker = get_object_or_404(Worker, pk=pk)
        serializer = UserBlockSerializer(
            worker.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, 200)
        return Response(serializer.errors, 400)


class CustomersViewSet(viewsets.ModelViewSet):

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # authentication_classes = (TokenAuthentication,)
    model = Customer
    permission_classes = (CustomerAccessPolicy,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Method to get a list of customers"
                              " within your access",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: CustomerSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of customers.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Creating a new user in the system as customer",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new customer.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Method to get customer object. This user "
                              "method is installed in the system as the "
                              "customer of the service.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: CustomerSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve customer.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Updating a customer object in the system",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update customer.
        """
        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Updating individual customer fields in the "
                              "system",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial customer update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Customers'],
        operation_description="Removing a customer record from the system",
        responses=base_swagger_responses(204, 401, 403, 404)
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Delete customer.
        """
        return super().destroy(request, pk, *args, **kwargs)


class TasksViewSet(CustomSerializerClassMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (TasksAccessPolicy,)
    action_serializers = {
        'list': TaskListSerializer
    }

    # @method_decorator(cache_page(60 * 60 * 2))
    @swagger_auto_schema(
        tags=['Tasks'],
        operation_description="Method to get a list of tasks "
                              "within your access",
        manual_parameters=[
            openapi.Parameter(
                'role',
                openapi.IN_QUERY,
                description="Getting tasks by role",
                type=openapi.TYPE_STRING,
                enum=['WORKER', 'CUSTOMER']
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Getting tasks by status",
                type=openapi.TYPE_STRING,
                enum=configs.TASK_STATUSES + ['IN_PROCESS'],
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date received tasks from. Format "
                            "(2019-07-29T21:00:00Z)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date received tasks to. "
                            "Format (2019-07-29T21:00:00Z)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses=base_swagger_responses(
            204, 400, 401, 403, kparams={200: TaskListSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of tasks.
        """
        user = request.user
        role = request.GET.get('role')
        status = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_from = get_datetime_obj(date_from)
        date_to = request.GET.get('date_to')
        date_to = get_datetime_obj(date_to)

        if hasattr(user, 'worker') and user.groups.filter(
                name='Worker').exists() and role == 'WORKER':
            self.queryset = user.worker.tasks

        if hasattr(user, 'customer') and user.groups.filter(
                name='Customer').exists() and role == 'CUSTOMER':
            self.queryset = user.customer.tasks

        if status == 'IN_PROCESS':
            self.queryset = self.queryset.filter(
                status__in=configs.TASK_STATUSES_PROCESS
            )
        elif status:
            self.queryset = self.queryset.filter(
                status=status
            )

        if date_from and date_to:
            self.queryset = self.queryset.filter(
                created_at__range=(date_from, date_to)
            )

        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tasks'],
        operation_description="Creating a new task",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new task.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tasks'],
        operation_description="Method to get task object. Can only be created "
                              "by Сustomer.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: TaskSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve task.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tasks'],
        operation_description="Updating a task object in the system. "
                              "Can only be updated by Сustomer or Manager.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update task.
        """

        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tasks'],
        operation_description="Updating individual task fields in the "
                              "system. Can only be updated by Сustomer or "
                              "Manager.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial task update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    # TODO: without with this method
    # @swagger_auto_schema(
    #     tags=['Tasks'],
    #     operation_description="Deactivated system record. Not "
    #                           "deleted from the database. Historical entity",
    #     responses=base_swagger_responses(200, 401, 403, 404)
    # )
    # def destroy(self, request, pk=None, *args, **kwargs):
    #     """
    #     Deactivate task.
    #     """
    #     return super().destroy(request, pk, *args, **kwargs)


class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    model = Service
    permission_classes = (ServicesAccessPolicy,)

    @swagger_auto_schema(
        tags=['Services'],
        operation_description="Method to get a list of services",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: ServiceSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of services.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Services'],
        operation_description="Creating a new service",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new service.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Services'],
        operation_description="Method to get service object.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: ServiceSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve service.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Services'],
        operation_description="Updating a service object in the system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update task.
        """
        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Services'],
        operation_description="Updating individual service fields in the "
                              "system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial task update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Services'],
        #  TODO: выяснить что будет происходить с этим методом
        operation_description="Deactivated system record. Not deleted from "
                              "the database. Historical entity",
        responses=base_swagger_responses(200, 401, 403, 404)
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Deactivate task.
        """
        return super().destroy(request, pk, *args, **kwargs)


class PlaceViewSet(CustomSerializerClassMixin, viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = (PlaceAccessPolicy,)
    action_serializers = {
        'list': PlaceListSerializer
    }

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Method to get a list of places",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: PlaceListSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of places.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Creating a new place",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new place.
        """
        file = None
        if request.POST:
            data = request.data
            if request.accepted_media_type == 'multipart/form-data':
                data = json.loads(request.POST.get('data'))
                file = request.FILES.get('file')

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                if file:
                    url = upload_to_backet(file)
                    serializer.validated_data['image_url'] = url
                serializer.save()
                return Response(serializer.data, 201)
            return Response(serializer.errors, 400)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Method to get place object.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: PlaceSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve place.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Updating a place object in the system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update place.
        """
        if request.POST:
            place = self.get_object()
            data = json.loads(request.POST.get('data'))
            file = request.FILES.get('file')
            serializer = self.serializer_class(place, data=data)
            if serializer.is_valid():
                if file:
                    url = upload_to_backet(file)
                    serializer.validated_data['image_url'] = url
                serializer.save()
                return Response(serializer.data, 200)
            return Response(serializer.errors, 400)
        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Updating individual place fields in the "
                              "system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial task update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Places'],
        operation_description="Deactivated system record. Not deleted from "
                              "the database. Historical entity",
        responses=base_swagger_responses(200, 401, 403, 404)
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Deactivate place.
        """
        return super().destroy(request, pk, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    model = User
    serializer_class = UserSerializer
    permission_classes = (UserAccessPolicy,)

    @swagger_auto_schema(
        tags=['users'],
        operation_description="Creating a new user",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new service.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['users'],
        operation_description="Method to get place object.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: UserSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve place.
        """

        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['users'],
        operation_description="Block user",
        request_body=UserBlockSerializer,
        responses=base_swagger_responses(200, 401, 403, 404)
    )
    @action(methods=["PATCH"], detail=True)
    def block(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        serializer = UserBlockSerializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, 200)
        return Response(serializer.errors, 400)


class ReviewViewSet(CustomSerializerClassMixin, viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = WorkerCustomerReviewSerializer
    permission_classes = (ReviewAccessPolicy,)
    action_serializers = {
        'update': ReviewUpdateSerializer
    }

    @swagger_auto_schema(
        tags=['review'],
        operation_description="Method to get a list of reviews by worker.",
        manual_parameters=[
            openapi.Parameter(
                'worker',
                openapi.IN_QUERY,
                description="List of reviews by worker",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses=base_swagger_responses(
            204, 401, 403,
            kparams={200: WorkerCustomerReviewSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        worker_id = request.GET.get('worker')
        if worker_id:
            worker = Worker.objects.get(id=worker_id)
            serializer = WorkerCustomerReviewSerializer(
                worker.worker_reviews.all(), many=True
            )
            if serializer.data:
                return Response(serializer.data, status=200)
            return Response(serializer.data, status=204)

        reviews = CustomerReview.objects.filter(
            worker__in=Worker.objects.values_list('id', flat=True)
        )
        serializer = WorkerCustomerReviewSerializer(reviews, many=True)
        if serializer.data:
            return Response(serializer.data, status=200)
        return Response(serializer.data, status=204)

    @swagger_auto_schema(
        tags=['review'],
        operation_description="Creating a new review for worker",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['review'],
        operation_description="Creating a new review for worker",
        responses=base_swagger_responses(200, 400, 401, 403)
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

# TODO: Review for Place, maybe future
# class ListPlaceCustomerReview(APIView):
#
#     @swagger_auto_schema(
#         tags=['Review'],
#         request_body=PlaceCustomerReviewSerializer,
#         operation_description="Creating a new review for place.",
#         responses=base_swagger_responses(201, 400, 401, 403)
#     )
#     def post(self, request):
#         serializer = PlaceCustomerReviewSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'status': "Created"}, status=201)
#         return Response({'error': serializer.errors}, status=400)
#
#     @swagger_auto_schema(
#         tags=['Review'],
#         operation_description="List of reviews by place",
#         manual_parameters=[
#             openapi.Parameter(
#                 'place',
#                 openapi.IN_QUERY,
#                 description="List of reviews by place",
#                 type=openapi.TYPE_INTEGER
#             )
#         ],
#         responses=base_swagger_responses(
#             204, 401, 403,
#             kparams={200: PlaceCustomerReviewSerializer(many=True)}
#         )
#     )
#     def get(self, request):
#         place_id = request.GET.get('place')
#         if place_id:
#             place = get_object_or_404(Place, pk=place_id)
#             serializer = PlaceCustomerReviewSerializer(
#                 place.place_reviews.all(), many=True
#             )
#             if serializer.data:
#                 return Response(serializer.data, status=200)
#             return Response(serializer.data, status=204)
#
#         reviews = CustomerReview.objects.filter(
#             place__in=Worker.objects.values_list('id', flat=True)
#         )
#         serializer = PlaceCustomerReviewSerializer(reviews, many=True)
#         if serializer.data:
#             return Response(serializer.data, status=200)
#         return Response(serializer.data, status=204)


class TaskItemViewSet(viewsets.ModelViewSet):
    queryset = TaskItem.objects.all()
    serializer_class = TaskItemSerializer

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Method to get a list of task Items",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: TaskItemSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of task Items.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Creating a new task item",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new task item.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Method to get task item object.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: TaskItemSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve task item.
        """
        return super().retrieve(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Updating a task item object in the system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update task item.
        """
        return super().update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Updating individual task item fields in the "
                              "system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Partial task update.
        """
        return super().partial_update(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Task Item'],
        operation_description="Deactivated system record. Not deleted from "
                              "the database. Historical entity",
        responses=base_swagger_responses(200, 401, 403, 404)
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Deactivate task item.
        """
        return super().destroy(request, pk, *args, **kwargs)


class TypeViewSet(viewsets.ModelViewSet):
    permission_classes = (TypeAccessPolicy,)
    queryset = Types.objects.all()
    serializer_class = TypeSerializer


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = (ProductAccessPolicy,)
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @swagger_auto_schema(
        tags=['products'],
        operation_description="Creating a new product",
        responses=base_swagger_responses(201, 400, 401, 403)
    )
    def create(self, request, *args, **kwargs):
        """
        Create new product.
        """
        if request.POST:
            data = json.loads(request.POST.get('data'))
            file = request.FILES.get('file')
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                if file:
                    url = upload_to_backet(file)
                    serializer.validated_data['image_url'] = url
                serializer.save()
                return Response(serializer.data, 201)
            return Response(serializer.errors, 400)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['products'],
        operation_description="Updating a product item object in the system.",
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def update(self, request, pk=None, *args, **kwargs):
        """
        Update task item.
        """
        if request.POST:
            place = self.get_object()
            data = json.loads(request.POST.get('data'))
            file = request.FILES.get('file')
            serializer = self.serializer_class(place, data=data)
            if serializer.is_valid():
                if file:
                    url = upload_to_backet(file)
                    serializer.validated_data['image_url'] = url
                serializer.save()
                return Response(serializer.data, 200)
            return Response(serializer.errors, 400)
        return super().update(request, pk, *args, **kwargs)


class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = (AddressAccessPolicy,)
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    @swagger_auto_schema(
        tags=['addresses'],
        operation_description="Method to get a list of task Addresses",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: TaskItemSerializer(many=True)}
        )
    )
    def list(self, request, *args, **kwargs):
        """
        Return a list of task Items.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['addresses'],
        operation_description="Method to get task item address.",
        responses=base_swagger_responses(
            400, 401, 403, 404, kparams={200: TaskItemSerializer}
        )
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve task item.
        """
        return super().retrieve(request, pk, *args, **kwargs)
