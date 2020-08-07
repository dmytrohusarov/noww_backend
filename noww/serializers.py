from moneyed import Money
from rest_framework import serializers, exceptions
from django.db import transaction, utils
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from .models import Worker as WorkerModel
from .models import *
from .models import (Worker, Customer, Task, Service, Place, Address, Review,
                     User as UserModel, Product, TaskItem, Types)
from django.contrib.auth.validators import UnicodeUsernameValidator


def get_group(name:str):
    return Group.objects.filter(name=name).first()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = (
            'id', 'avatar_url', 'email', 'first_name', 'last_name',
            'phone_number', 'date_joined', 'groups'
        )
        ref_name = None

        extra_kwargs = {
            'phone_number': {
                'validators': [UnicodeUsernameValidator()],
            },
            'groups': {
                'read_only': True
            }
        }

    def create(self, validate_data):
        validate_data.pop('avatar', None)  # Add user without avatar
        instance = UserModel.objects.create(**validate_data)
        return instance


class UserBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active',)


class WorkerApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ('is_verified',)


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = Address
        fields = "__all__"


class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'description', 'status')


class DocSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(DocSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Doc
        fields = ("id", "url", "name", "description")

    def create(self, validated_data):
        worker = self.context['worker']
        validated_data.update({'worker_id': worker.id})
        doc_id = validated_data.get('id')
        if doc_id:
            doc = get_object_or_404(Doc, pk=doc_id)
            doc.__dict__.update(**validated_data)
        else:
            doc = Doc.objects.create(**validated_data)
        return doc

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "url": instance.url,
            "name": instance.name,
            "description": instance.description,
        }


class DocDeleteSerializer(serializers.Serializer):
    doc_ids = serializers.ListField(child=serializers.IntegerField())

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class WorkerSerializer(serializers.ModelSerializer):
    tasks = TasksSerializer(many=True, read_only=True, required=False)
    user = UserSerializer(many=False)
    docs = DocSerializer(
        many=True, required=False, allow_null=True,
        help_text="Creating new objects can be transferred to the collection "
                  "according to the scheme. If you want to update previously "
                  "created records, then you need to transfer the ID of "
                  "previously created records to the object. If you pass an "
                  "empty collection or without transferring data about old "
                  "objects, then objects that are not in the list are deleted "
    )
    rate = serializers.ReadOnlyField()
    profit = serializers.ReadOnlyField()

    class Meta:
        model = WorkerModel
        fields = '__all__'
        ref_name = None

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        phone_number = user_data['phone_number']
        user = UserModel.objects.get(phone_number=phone_number)

        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.email = user_data['email']
        user.groups.add(get_group('Worker'))
        user.save()

        worker = Worker.objects.create(
            user=user,
            device=validated_data['device']
        )
        return worker

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        user_data = validated_data.pop('user', None)
        docs_data = validated_data.pop('docs', [])

        if user_data:
            user.__dict__.update(**user_data)
            user.save()
        instance.__dict__.update(**validated_data)
        instance.save()

        exist_docs = []
        for doc_data in docs_data:
            doc = {
                "id": doc_data.get('id'),
                "url": doc_data.get('url'),
                "name": doc_data.get('name'),
                "description": doc_data.get('description')
            }
            if doc['id']:
                doc_ = get_object_or_404(Doc, pk=doc['id'])
                # TODO: detail json output exception(now "detail": "Not found."
                doc_.__dict__.update(**doc)
            else:
                doc_ = instance.docs.create(**doc)
            doc_.save()
            exist_docs.append(doc_)
        not_needed_doc = set(instance.docs.all()).difference(exist_docs)
        not_needed_doc_ids = [doc.id for doc in not_needed_doc]
        Doc.objects.filter(id__in=not_needed_doc_ids).delete()
        return instance


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    profit = serializers.ReadOnlyField()
    addresses = AddressSerializer(
        many=True, help_text="If you pass objects, then by default in "
                             "default_address_id there will be a created "
                             "address"
    )

    class Meta:
        model = Customer
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        phone_number = user_data['phone_number']
        user = UserModel.objects.get(phone_number=phone_number)
        user.__dict__.update(**user_data)
        user.groups.add(get_group("Customer"))

        instance = Customer.objects.create(
            user=user,
            device=validated_data['device'],
            created_by=validated_data.get('created_by')
        )

        addresses = validated_data.pop('addresses', [])
        _addresses = []
        for address in addresses:
            if address.get('id'):
                try:
                    # get or create if id exist and data in address changed
                    _address, _ = instance.addresses.get_or_create(**address)
                except utils.IntegrityError:
                    # if does not exist, get or create without id
                    address.pop('id')
                    _address, _ = instance.addresses.get_or_create(**address)
            else:
                _address, _ = instance.addresses.get_or_create(**address)
            _addresses.append(_address)
        instance.addresses.set(_addresses)
        if instance.addresses.exists():
            instance.default_address_id = instance.addresses.first().id
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user = instance.user
        user.__dict__.update(**user_data)
        user.save()

        addresses = validated_data.pop('addresses', [])
        _addresses = []
        for address in addresses:
            if address.get('id'):
                try:
                    # get or create if id exist and data in address changed
                    _address, _ = instance.addresses.get_or_create(**address)
                except utils.IntegrityError:
                    # if does not exist, get or create without id
                    address.pop('id')
                    _address, _ = instance.addresses.get_or_create(**address)
            else:
                _address, _ = instance.addresses.get_or_create(**address)
            _addresses.append(_address)
        instance.addresses.set(_addresses)
        instance.__dict__.update(**validated_data)
        instance.save()
        return instance


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class TypeSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Types
        fields = '__all__'

    def get_parent_name(self, type_):
        parent_name_ = type_.parent.name if type_.parent else None
        return parent_name_


class SubTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Types
        fields = ('id', 'name', 'parent')


class ProductSerializer(serializers.ModelSerializer):
    imageUrl = serializers.URLField(
        source="image_url", required=False, allow_null=True, allow_blank=True
    )
    time = serializers.ReadOnlyField(default=60)
    stars = serializers.ReadOnlyField(default=90)

    kinds = TypeSerializer(many=True, required=False, read_only=True)
    kind_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Types.objects.all(), source='kinds'
    )
    subkinds = TypeSerializer(
        many=True, required=False, source="sub_kinds", read_only=True
    )
    subkind_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Types.objects.all(),
        source='sub_kinds'
    )

    class Meta:
        model = Product
        fields = (
            'imageUrl',
            'title',
            'description',
            'time',
            'price',
            'stars',
            'kinds',
            'kind_ids',
            'subkinds',
            'subkind_ids',
            'id',
            'price_currency'
        )

    @transaction.atomic
    def create(self, validated_data):
        kinds = validated_data.pop('kinds', [])
        subkinds = validated_data.pop('sub_kinds', [])
        instance = Product.objects.create(**validated_data)
        instance.kinds.set(kinds)
        instance.sub_kinds.set(subkinds)
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        kinds = validated_data.pop('kinds')
        instance.kinds.set(kinds)
        subkinds = validated_data.pop('sub_kinds')
        instance.sub_kinds.set(subkinds)
        instance.__dict__.update(**validated_data)
        instance.save()
        return instance


class StringListField(serializers.ListField):
    child = serializers.CharField()


class PlaceSerializer(serializers.ModelSerializer):
    time = serializers.ReadOnlyField(default=60)
    stars = serializers.ReadOnlyField(default=90)
    imageUrl = serializers.URLField(
        source="image_url", required=False, allow_null=True, allow_blank=True,
        read_only=True
    )
    kinds = TypeSerializer(many=True)
    subkinds = TypeSerializer(many=True, source="sub_kinds")
    addresses = AddressSerializer(many=True, read_only=True)
    address_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Address.objects.all(),
        source='addresses'
    )
    products = ProductSerializer(
        many=True, read_only=True, source='place_to_product'
    )
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Product.objects.all(),
        source='place_to_product'
    )

    class Meta:
        model = Place
        fields = (
            'imageUrl',
            'title',
            'description',
            'time',
            'stars',
            'kinds',
            'subkinds',
            'addresses',
            'address_ids',
            'id',
            'products',
            'product_ids',
        )

    @transaction.atomic
    def create(self, validated_data):
        addresses = validated_data.pop('addresses', [])
        products = validated_data.pop('place_to_product')
        instance = Place.objects.create(**validated_data)
        instance.addresses.set(addresses)
        instance.place_to_product.set(products)
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        addresses = validated_data.pop('addresses')
        instance.addresses.set(addresses)
        products = validated_data.pop('place_to_product')
        instance.place_to_product.set(products)
        instance.__dict__.update(**validated_data)
        instance.save()
        return instance


class PlaceListSerializer(PlaceSerializer):
    class Meta:
        model = Place
        fields = (
            'imageUrl',
            'title',
            'description',
            'time',
            'stars',
            'addresses',
            'address_ids',
            'id',
        )


class TaskItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='product', queryset=Product.objects.all())

    class Meta:
        model = TaskItem
        fields = ('id', 'product', 'product_id', 'quantity')


class TaskWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    image = serializers.ReadOnlyField(default='Mock')
    total_money = serializers.SerializerMethodField()
    worker_rate = serializers.ReadOnlyField(default=90)
    currency = serializers.SerializerMethodField()
    items = TaskItemSerializer(source='task_to_product', many=True)
    customer_address = AddressSerializer(many=False)

    task_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), many=False, source='task_address',
        write_only=True
    )
    task_address = AddressSerializer(many=False, read_only=True)

    place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.all(), many=False, source='place',
        write_only=True
    )
    place = PlaceSerializer(many=False, read_only=True)

    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), many=False, source='service',
        write_only=True
    )
    service = ServiceSerializer(many=False, read_only=True)

    # worker_id = serializers.PrimaryKeyRelatedField(
    #     queryset=Worker.objects.all(), many=False, source='worker',
    #     write_only=True
    # )
    worker = TaskWorkerSerializer(many=False, read_only=True)

    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), many=False, source='customer',
        write_only=True
    )
    customer = CustomerSerializer(many=False, read_only=True)

    class Meta:
        model = Task
        fields = (
            'place',
            'place_id',
            'title',
            'image',
            'description',
            'status',
            'duration',
            'weight',
            'task_address',
            'task_address_id',
            'customer_address',
            'created_at',
            'pay_type',
            'delivery_cost',
            'product_cost',
            'total_money',
            'note',
            'worker',
            # 'worker_id',
            'service',
            'service_id',
            'worker_rate',
            'status',
            'id',
            'currency',
            'items',
            'customer',
            'customer_id',
        )

    def get_total_money(self, task):
        return task.get_total_money()

    def get_currency(self, task):
        return task.product_cost_currency

    def create(self, validated_data):
        """
          'title',
          'image', - mock
          'description',
          'duration',
          'weight',
          'task_address',
          'customer_address',
          'created_at',
          'pay_type',
          'delivery_cost',
          'product_cost',
          'total_money',
          'note',
          'worker_id',
          'worker_rate',
          'status',
          'id',
          'currency',
          'items'
        """
        task_data = validated_data
        title = task_data['title']
        desc = task_data['description']
        duration = task_data['duration']
        weight = task_data['weight']
        pay_type = task_data['pay_type']
        note = task_data['note']
        service = task_data['service']
        customer = task_data['customer']
        task_address = task_data['task_address']
        place = task_data['place']

        customer_address = validated_data.pop('customer_address')
        c_address = Address.objects.get_or_create(
            **customer_address
        )
        customer_address = c_address[0]

        delivery_cost = Money(task_data['delivery_cost'])
        product_cost = Money(task_data['product_cost'])
        if self.initial_data.get('currency'):
            delivery_cost.currency = self.initial_data.get('currency')
            product_cost.currency = self.initial_data.get('currency')

        task = Task.objects.create(
            description=desc,
            title=title,
            duration=duration,
            weight=weight,
            pay_type=pay_type,
            delivery_cost=delivery_cost,
            product_cost=product_cost,
            note=note,
            service=service,
            customer=customer,
            place=place,
            customer_address=customer_address,
            task_address=task_address
        )
        task_items = task_data["task_to_product"]
        for items in task_items:
            s = TaskItem.objects.create(
                task=task,
                product=items['product'],
                quantity=items['quantity']
            )
            s.save()

        task.save()
        return task

    def update(self, instance, validated_data):
        items_validated_data = validated_data.pop('task_to_product')
        instance.description = validated_data.get('description',
                                                  instance.description),
        instance.title = validated_data.get('title', instance.title),
        instance.duration = validated_data.get('duration', instance.duration),
        instance.weight = validated_data.get('weight', instance.weight),
        instance.pay_type = validated_data.get('pay_type', instance.pay_type),
        instance.delivery_cost.amount = float(
            validated_data.get('delivery_cost',
                               instance.delivery_cost.amount)),
        instance.product_cost.amount = validated_data.get('product_cost',
                                                          instance.product_cost.amount),
        instance.note = validated_data.get('note', instance.note),
        instance.status = validated_data.get('status', instance.status),
        instance.worker.pk = validated_data.get('worker', instance.worker.pk),
        instance.service.pk = validated_data.get('service',
                                                 instance.service.pk),
        instance.customer.pk = validated_data.get('customer',
                                                  instance.customer.pk)

        place_id = validated_data.get('place_id', None)
        if place_id:
            instance.place.pk = validated_data.get('place_id')

        task_address = validated_data.pop('task_address')
        address = Address.objects.get(pk=task_address['id'])
        address.address = task_address['address']
        address.save()  # TODO include other fields

        customer_address = validated_data.pop('customer_address')
        address = Address.objects.get(pk=customer_address['id'])
        address.address = customer_address['address']
        address.save()  # TODO include other fields

        for each in items_validated_data:
            item_id = each.get('id', None)
            if item_id:
                prod_item = TaskItem.objects.get(id=item_id, task=instance)
                prod_item.product = each.get('product', prod_item.product)
                prod_item.quantity = each.get('quantity', prod_item.quantity)
                prod_item.save()
            else:
                TaskItem.objects.create(task=instance, **each)

        task = Task.objects.get(pk=instance.id)
        return task


class ProductItemTaskListSerializer(serializers.ModelSerializer):
    imageUrl = serializers.URLField(
        source="image_url", required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'imageUrl',
            'title',
        )


class ItemTaskListSerializer(TaskItemSerializer):
    product = ProductItemTaskListSerializer(many=False)

    class Meta:
        model = TaskItem
        fields = ("id", "quantity", "product")


class TaskListSerializer(TaskSerializer):
    items = ItemTaskListSerializer(source='task_to_product', many=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'image',
            'description',
            'status',
            'duration',
            'weight',
            'created_at',
            'pay_type',
            'delivery_cost',
            'product_cost',
            'total_money',
            'worker_rate',
            'status',
            'currency',
            'items'
        )


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"

    def create(self, validated_data):
        review_data = validated_data.pop('customer_reviews')
        review = Review.objects.create(**validated_data)
        customer_review = CustomerReview.objects.create(review=review,
                                                        **review_data)
        return customer_review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('description',)


class WorkerCustomerReviewSerializer(serializers.ModelSerializer):
    review = ReviewSerializer(many=False)

    class Meta:
        model = CustomerReview
        fields = ("worker", "review")

    def create(self, validated_data):
        user = self.context['request'].user
        if hasattr(user, 'customer') and user.groups.filter(name='Customer').exists():
            review_data = validated_data.pop('review')
            review_data['customer'] = user.customer
            review = Review.objects.create(**review_data)
            worker = validated_data.pop('worker')
            customer_review = CustomerReview.objects.create(
                review=review, worker=worker
            )
            return customer_review
        raise exceptions.PermissionDenied('Only a customer can leave a review')

    def update(self, instance, validated_data):

        user = self.context['request'].user
        if hasattr(user, 'customer') and user.groups.filter(name='Customer').exists():
            review = validated_data.pop('review')
            instance.description = review.get('description')
            instance.save()
            return instance.customer_review
        raise exceptions.PermissionDenied('Only a customer can update a review')


class PlaceCustomerReviewSerializer(serializers.ModelSerializer):
    review = ReviewSerializer(many=False)

    class Meta:
        model = CustomerReview
        fields = ("place", "review")

    def create(self, validated_data):
        review_data = validated_data.pop('review')
        review = Review.objects.create(**review_data)
        place = validated_data.pop('place')
        customer_review = CustomerReview.objects.create(
            review=review, place=place
        )
        return customer_review


class CustomerReviewSerializer(serializers.ModelSerializer):
    review = ReviewSerializer(many=False)
    place = PlaceSerializer(many=False)
    worker = WorkerSerializer(many=False)

    class Meta:
        model = CustomerReview
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_null=True,
                                 allow_blank=True)

    class Meta:
        model = Group
        fields = ("id", "name",)


class UserGroupAccessSerializer(serializers.Serializer):
    groups = GroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Group.objects.all(),
        source='groups'
    )

    class Meta:
        model = User
        fields = ("id", "groups", "group_ids")

    def update(self, instance, validated_data):
        return instance
