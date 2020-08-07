from django.urls import path

from .views import *

app_name = 'admin_reports'

urlpatterns = [
    path('reviews/', ReviewList.as_view(), name="reviews"),
    path('reviews/<int:review_id>/', ReviewRetrieve.as_view(),
         name="detail-review"),
    path('tasks/', TaskList.as_view(), name="tasks"),
    path('tasks/<int:id>/', TaskRetrieve.as_view(), name="task"),
    path('customer/<int:id>/', CustomerRetrieve.as_view(), name="customer"),
    path('customer_tasks/<int:customer_id>/', CustomerTasks.as_view()),

    path('workers_chart/', ReportWorkersChart.as_view()),
    path('worker_chart/<int:worker_id>/', ReportWorkerChart.as_view()),
    path('customers_chart/', ReportCustomersChart.as_view()),
    path('reviews_chart/', ReportReviewsChart.as_view()),
    path('tasks_chart/', ReportTasksChart.as_view()),

    path('home_statistic/', ReportHomeStatistics.as_view()),

]
