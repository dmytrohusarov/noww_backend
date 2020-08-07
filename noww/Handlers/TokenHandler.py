from rest_framework import status as ResponseStatus
from rest_framework.views import APIView
from rest_framework.response import Response

import noww.models

from noww.Handlers.WorkerHandler import WorkerHandlerClass

from pyfcm import FCMNotification
import nowwapi.settings as settings

from django.shortcuts import get_object_or_404

from Common.configs import TASK_STATUSES_FINAL
import logging
import sys

logger = logging.getLogger()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

message_title = "API Create task"
push_service = FCMNotification(api_key=settings.PUSH_NOTIFICATIONS_SETTINGS['FCM_API_KEY'])


def push_builder(task, rejected, token):
    """
    def function for the default fcm format
    :param task:
    :param rejected:
    :param token:
    :return:
    """
    return {
        "message": {
            "token": f"{token}",
            "mutable_content": True,
            "notification": {
                "title": "NEW_TASK",
                "body": f"New task: {task.description}"
            },
            "data": {
                "task": task.pk,
                "service": task.service.name,
                "w_rejs": rejected
            },
            "apns": {
                "headers": {
                    "apns-priority": "10",
                },
                "payload": {
                    "aps": {
                        "category": "NEW_TASK",
                        "alert": {
                            "body": f"New task: {task.description}"
                        },
                        "badge": 1,
                        "sound": "alert.aiff"
                    }}
            }
        }
    }


class TaskHandler(APIView):
    """
    processing requests for order request workers handler and decline codes
    """

    @staticmethod
    def put(request):
        """
        method for decline codes. method set statuses depends on the status code
        :param request: consists of pk and status fields
        :return:
        """
        pk = request.data.get('pk')  # TODO pk from the parameters
        task = noww.models.Task.objects.get(pk=pk)
        if task:
            status = request.data['status']
            if status in TASK_STATUSES_FINAL:
                task.status = status
            else:
                status_code = get_object_or_404(noww.models.Dictionary, name=status)
                if status_code.type == 'WORKER_DECLINES':
                    task.status = "CANCELLEDBYWORKER"
                elif status_code.type == 'CUSTOMER_DECLINES':
                    task.status = "CANCELLEDBYCUSTOMER"
                task.reject_code = status_code.name
            task.save()
            return Response(status=ResponseStatus.HTTP_200_OK)
        else:
            return Response(status=ResponseStatus.HTTP_404_NOT_FOUND)

    @staticmethod
    def post(request):
        """
        method for processing order request - processing with workers
        :param request: worker_id, token, w_rejs
        :return:
        """
        try:
            pk = request.data.get("worker_id")
            worker = get_object_or_404(noww.models.Worker, pk=pk)

            token_answer = request.data.get('token')
            task_id, status = token_answer.split("_")
        except Exception as e:
            logger.error("problem with post requst", e)

        task = get_object_or_404(noww.models.Task, pk=task_id)
        if task and status == "ACCEPTED":
            task.worker = worker
            task.status = 'IN_PROGRESS'
            task.save()
            return Response(status=ResponseStatus.HTTP_200_OK)
        elif task and status != "ACCEPTED":
            if 'w_rejs' in request.data:
                if request.data['w_rejs'] != "":
                    worker_rejected = str(request.data['w_rejs'])
                    worker_rejected += f',{request.data["worker_id"]}'
                else:
                    worker_rejected = str(request.data["worker_id"])
            else:
                worker_rejected = request.data["worker_id"]
            OrderRequest(lat=task.task_address.latitude,
                         lon=task.task_address.longitude, task_id=task_id,
                         rejected=worker_rejected)

            # TODO exclude rejeted ids from worker list
            return Response("ok", status=ResponseStatus.HTTP_200_OK)


class OrderRequest():

    def __init__(self, lat, lon, task_id, rejected=""):
        self.active_worker = 0
        self.lat = float(lat)
        self.lon = float(lon)
        self.worker = self.get_worker(self.lat, self.lon, rejected)
        self.task = task_id
        self.send_notify(self.worker, self.task, rejected)

    @staticmethod
    def get_worker(lat, lon, rejected):
        current_worker = WorkerHandlerClass.get_worker(lat, lon, rejected)
        return current_worker

    @staticmethod
    def send_notify(worker, task: str, rejected=""):
        try:
            task_id = int(task)
            task = noww.models.Task.objects.get(pk=task_id)

            worker_id = int(worker[0]['worker_id'])
            worker = get_object_or_404(noww.models.Worker, pk=worker_id)

            token = worker.device
            # payload = push_builder(task, rejected, token)  # TODO tests for fcm push
            WorkerHandlerClass.set_workertask(worker_id, task_id)

            # extra = {"task": task_id, "service": task.service.name,
            #          "description": task.description, "w_rejs": rejected}
            message_body = f"New task: {task.description}"
            payload = {"task": task_id, "service": task.service.name,
                       "description": task.description, "w_rejs": rejected}

            # TODO android/ios switch
            result = push_service.notify_single_device(registration_id=token,
                                                       message_title=message_title,
                                                       message_body=message_body,
                                                       data_message=payload,
                                                       low_priority=False,
                                                       content_available=True)
            print(worker_id, payload, result)
        except Exception as e:
            logger.error("error with notification", e, " worker_id", worker_id)


if __name__ == "__main__":
    OrderRequest(55.4390000, 30.52587120000001, 1)
