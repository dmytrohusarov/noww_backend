import re
from rest_framework import status
from django.contrib.auth.models import Group
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Customer, Worker
from .serializers import GroupSerializer, UserGroupAccessSerializer

from nowwapi.utils import base_swagger_responses, upload_to_backet

from drf_yasg.utils import swagger_auto_schema


class CustomAuthToken(ObtainAuthToken):

    @swagger_auto_schema(
        tags=['auth'],
        request_body=ObtainAuthToken.serializer_class,
        operation_description="Response auth token",
        responses=base_swagger_responses(200, 400, 401, 403)
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not password or password != "0000":
            return Response({"invalid password"}, status.HTTP_400_BAD_REQUEST)
        if re.match(r'^\+?1?\d{9,15}$', username):
            user, _ = User.objects.get_or_create(phone_number=username)
            token, _ = Token.objects.get_or_create(user=user)

            try:
                customer = Customer.objects.get(user=user).pk
            except Customer.DoesNotExist:
                customer = ''

            worker = Worker.objects.filter(user=user).first()
            if worker:
                worker = worker.pk
            else:
                worker = ''

        else:
            return Response({"invalid phone number"}, status.HTTP_400_BAD_REQUEST)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'phone_number': user.phone_number,
            'customer_id': customer,
            'worker_id': worker,
            'is_staff': user.is_staff,
        }, status.HTTP_200_OK)


class ImageViewSet(APIView):

    def post(self, request, *args, **kwargs):
        file = request.FILES['file']
        url = upload_to_backet(file)
        return Response({'imageUrl': url}, status=200)


class AccessGroupView(APIView):

    @swagger_auto_schema(
        tags=['access'],
        operation_description="",
        responses=base_swagger_responses(
            204, 401, 403, kparams={200: GroupSerializer(many=True)}
        )
    )
    def get(self, request):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, 200)


class UserGroupAccess(APIView):

    @swagger_auto_schema(
        tags=['access'],
        operation_description="",
        responses=base_swagger_responses(
            204, 401, 403, 404, kparams={200: GroupSerializer(many=True)}
        )
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = GroupSerializer(user.groups.all(), many=True)
        return Response(serializer.data, 200)

    @swagger_auto_schema(
        tags=['access'],
        operation_description="",
        request_body=UserGroupAccessSerializer,
        responses=base_swagger_responses(200, 400, 401, 403, 404)
    )
    def put(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = UserGroupAccessSerializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid():
            user.groups.set(serializer.validated_data['groups'])
            return Response(serializer.data, 200)
        return Response(serializer.errors, 400)
