from GeoFire.geofire import GeoFire
from Common import db_config

from geopy import distance
import datetime


class WorkerHandlerClass:
    instance = None

    def __new__(cls):
        if cls.instance is not None:
            return cls.instance
        else:
            inst = cls.instance = super(WorkerHandlerClass, cls).__new__()
            return inst

    def __init__(self, collection):
        pass

    @staticmethod
    def set_workertask(worker_id,task_id):
        db_config.worker_task.child(str(worker_id)).set({
            "id": task_id,
            "status": 1,
            "timestamp": int(datetime.datetime.utcnow().timestamp() * 1000)
        })


    @staticmethod
    def get_worker(lat, lon, rejected=""):

        rejs = []
        if rejected != "":
            rejs = list(map(int, rejected.split(",")))

        geofire = GeoFire(lat=lat,
                          lon=lon,
                          radius=10,
                          unit='km').config_firebase(
            api_key=db_config.api_key,
            auth_domain=db_config.auth_domain,
            database_URL=db_config.database_URL,
            storage_bucket=db_config.storage_bucket)

        result = geofire.query_nearby_objects(query_ref='worker_locations', geohash_ref='g')

        res = []
        distances = orderby_distance((lat, lon), [{'id': item, 'loc': result[item]['l']} for item in result])
        for item in distances:
            if int(item['id']) not in rejs:
                try:
                    w_info = db_config.worker_info.child(item['id']).get()
                    if w_info['is_ready']:
                        res.append({
                            "worker_id": item['id'],
                            "loc": result[item['id']]['l']
                        })
                        break
                except Exception as e:
                    print("error with worker_info:", item['id'], e)

        return res


def orderby_distance(center_point: tuple, workers: list):
    result = []
    for worker in workers:
        point_distance = distance.distance(center_point, worker['loc'])
        result.append({'id': worker['id'], 'distance': point_distance})

    result = sorted(result, key=lambda k: k['distance'])
    return result


if __name__ == "__main__":
    # d = WorkerHandlerClass.get_worker(50.4128784, 30.52587120000001)
    WorkerHandlerClass.set_workertask(1,2)
