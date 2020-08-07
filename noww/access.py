from rest_access_policy import AccessPolicy


class AddressAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "create", "update", "delete"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager",
                "group:Customer"
            ],
            "effect": "allow"
        },
        {
            "action": ["retrieve"],
            "principal": "*",
            "effect": "allow"
        },
    ]


class CustomerAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager"
            ],
            "effect": "allow",
        },
        {
            "action": ["create"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": ["retrieve"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager",
                "group:Customer"
            ],
            "effect": "allow",
            "condition": ["user_customer_owner"]
        },
        {
            "action": ["update"],
            "principal": ["group:Customer"],
            "condition": ["user_customer_owner"],
            "effect": "allow"
        },
        {
            "action": ["partial_update"],
            "principal": ["group:Administrator", "group:Support"],
            "effect": "allow"
        },
        {
            "action": ["delete"],
            "principal": ["group:Administrator"],
            "effect": "allow"
        },
    ]

    def user_customer_owner(self, request, view, action):
        customer = view.get_object()
        if request.user.groups.filter(name='Customer').exists():
            return customer.user == request.user
        return True


class PlaceAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Customer"
            ],
            "effect": "allow"
        },
        {
            "action": ["create", "delete"],
            "principal": [
                "group:Administrator", "group:Manager"
            ],
            "effect": "allow"
        },
        {
            "action": ["update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
            ],
            "effect": "allow"
        }
    ]


class ProductAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Customer"
            ],
            "effect": "allow"
        },
        {
            "action": ["create", "delete"],
            "principal": [
                "group:Administrator", "group:Manager"
            ],
            "effect": "allow"
        },
        {
            "action": ["update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
            ],
            "effect": "allow"
        },
    ]


class ReviewAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker", "group:Customer"
            ],
            "effect": "allow"
        },
        {
            "action": ["create"],
            "principal": ["group:Customer"],
            "effect": "allow"
        },
        {
            "action": ["update"],
            "principal": ["group:Administrator"],
            "effect": "allow",
        },
        {
            "action": ["delete"],
            "principal": ["group:Administrator"],
            "effect": "allow"
        },

    ]


class ServicesAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Customer"
            ],
            "effect": "allow"
        },
        {
            "action": ["create", "delete"],
            "principal": [
                "group:Administrator", "group:Manager"
            ],
            "effect": "allow"
        },
        {
            "action": ["update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
            ],
            "effect": "allow"
        },
    ]


# TODO: required discussion
class TasksAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker", "group:Customer"
            ],
            "effect": "allow",
            # "condition": "get_user_tasks" # TODO: check flow

        },
        {
            "action": ["create"],
            "principal": ["group:Customer"],
            "effect": "allow"
        },
        {
            "action": ["retrieve"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker", "group:Customer"
            ],
            "effect": "allow",
            # "condition": "user_customer_owner" # TODO: check flow
        },
        {
            "action": ["update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker", "group:Customer"
            ],
            "effect": "allow",
            "condition": "task_order"
        },
    ]

    @classmethod
    def scope_queryset(cls, request, qs):
        print(qs)
        return qs.filter(creato1r=request.user)

    # TODO: check flow
    # def get_user_tasks(self, request, view, action):
    #     user = request.user
    #     if hasattr(user, 'worker') and user.groups.filter(name='Worker').exists():
    #         return user.worker.tasks.all()

    # @classmethod
    # def scope_queryset(cls, request, qs):
    #     return qs.filter(creator=request.user)

    def task_order(self, request, view, action):
        # TODO: refactoring needed
        task = view.get_object()
        user = request.user
        if hasattr(user, 'worker') and user.groups.filter(
                name='Worker').exists():
            current_tasks = user.worker.get_current_tasks()
            return current_tasks
        if request.user.groups.filter(name='Worker').exists() and task.status is not 'COMPLETED':
            return task.user == request.user
        elif request.user.groups.filter(name='Customer').exists():
            return task.user == request.user
        return True

    # TODO: check flow
    # def user_worker_current_task(self, request, view, action):
    #     account = view.get_object()
    #     return True


class TypeAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve", "update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support"
            ],
            "effect": "allow"
        },
        {
            "action": ["create", "delete"],
            "principal": [
                "group:Administrator", "group:Manager"
            ],
            "effect": "allow"
        },
    ]


class UserAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve", "update"],
            "principal": [
                "group:Administrator", "group:Manager", "group:Support",
                "group:Worker", "group:Customer",
            ],
            "effect": "allow"
        },
        {
            "action": ["create"],
            "principal": ["anonymous"],
            "effect": "allow"
        },
        {
            "action": ["delete"],
            "principal": [
                "group:Administrator"
            ],
            "effect": "allow"
        },
        {
            "action": ["block"],
            "principal": ["group:Administrator", "group:Manager"],
            "effect": "allow"
        },
    ]


class WorkerAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager"
            ],
            "effect": "allow",
        },
        {
            "action": ["create"],
            "principal": [
                "*"
            ],
            "effect": "allow"
        },
        {
            "action": ["retrieve"],
            "principal": [
                "group:Administrator", "group:Support", "group:Manager",
                "group:Worker"
            ],
            "effect": "allow",
            "condition": "user_worker_owner"
        },
        {
            "action": ["update"],
            "principal": ["group:Worker"],
            "condition": "user_worker_owner",
            "effect": "allow"
        },
        {
            "action": ["partial_update"],
            "principal": ["group:Worker"],
            "condition": "user_worker_owner",
            "effect": "allow"
        },
        {
            "action": ["delete", "approve"],
            "principal": ["group:Administrator", "group:Manager"],
            "effect": "allow"
        },
    ]

    def user_worker_owner(self, request, view, action):
        worker = view.get_object()
        if request.user.groups.filter(name='Worker').exists():
            return worker.user == request.user
        return True
