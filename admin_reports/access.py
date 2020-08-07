from rest_access_policy import AccessPolicy


class BaseReportStaffAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ['*'],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support"
            ],
            "effect": "allow",
            "condition": ["manager"]

        }
    ]

    def manager(self, request, view, action):
        if request.method == 'GET' and view.request.user.is_staff:
            return True
        return False


class CustomerRetrieveAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["get"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Customer"
            ],
            "effect": "allow"
        }
    ]


class ReportWorkersChartAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["ReportWorkersChart"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager"
            ],
            "effect": "allow",
        }
    ]


class ReportCustomersChartAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["ReportCustomersChart"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Customer"
            ],
            "effect": "allow",
        }
    ]


class ReportTasksChartAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["ReportTasksChart"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker"
            ],
            "effect": "allow"
        }
    ]


class ReportReviewsChartAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["ReportReviewsChart"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker"
            ],
            "effect": "allow"
        }
    ]


class ReportWorkerChartAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["ReportWorkerChart"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker"
            ],
            "effect": "allow"
        }
    ]


class ReviewListAccessPolicy(BaseReportStaffAccessPolicy):
    pass


class ReviewRetrieveAccessPolicy(BaseReportStaffAccessPolicy):
    pass


class TaskListAccessPolicy(BaseReportStaffAccessPolicy):
    pass


class TaskRetrieveAccessPolicy(BaseReportStaffAccessPolicy):
    pass


class CustomerTasksAccessPolicy(BaseReportStaffAccessPolicy):
    pass


class ReportHomeStatisticsChartAccessPolicy(BaseReportStaffAccessPolicy):
    pass
