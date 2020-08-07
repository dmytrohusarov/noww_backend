api_key="AIzaSyBegvaryh20yEaOtXUK2hBsSpNUpWbXtgY"
auth_domain='mineral-anchor-249706'
database_URL='https://mineral-anchor-249706.firebaseio.com'
storage_bucket='mineral-anchor-249706'



import firebase_admin
from firebase_admin import credentials

import os
from firebase_admin import db

cred = credentials.Certificate(os.path.abspath(__file__+ "/../") + '/service.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mineral-anchor-249706.firebaseio.com/'
})
worker_info = db.reference().child('worker_info')
worker_task = db.reference().child('worker_task')