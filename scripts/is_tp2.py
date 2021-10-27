from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from flask_caching import Cache
import sim
import time 
import threading
import requests
#from firebase import firebase

app = Flask(__name__)
api = Api(app)

# Instantiate the cache
cache = Cache()
cache.init_app(app=app, config={"CACHE_TYPE": "filesystem",'CACHE_DIR': './tmp'})

# get firebase address
#firebase = firebase.FirebaseApplication("https://is-lab2-fc088-default-rtdb.europe-west1.firebasedatabase.app/", None)

# global configuration variables
clientID=-1
accel = [0,0,0]

# database structure
# db = {
#     'accel_x': {
#         'data': accel[0],
#         'timestamp': time.time()
#     },
#     'accel_y': {
#         'data': accel[1],
#         'timestamp': time.time()
#     },
#     'accel_z': {
#         'data': accel[2],
#         'timestamp': time.time()
#     },
#     'config': {
#         'current_rate': 1.0
#     }
# }

# Helper function provided by the teaching staff
def get_data_from_simulation(id):
    """Connects to the simulation and gets a float signal value

    Parameters
    ----------
    id : str
        The signal id in CoppeliaSim. Possible values are 'accelX', 'accelY' and 'accelZ'.

    Returns
    -------
    data : float
        The float value retrieved from the simulation. None if retrieval fails.
    """
    if clientID!=-1:
        res, data = sim.simxGetFloatSignal(clientID, id, sim.simx_opmode_blocking)
        if res==sim.simx_return_ok:
            return data
    return None

df_ref = 'https://is-lab2-fc088-default-rtdb.europe-west1.firebasedatabase.app/'

# TODO LAB 2 - Implement the necessary functions to read and write data to your Firebase real-time database
def push_data(child, data):  #create data
    print(f'CHILD: {child}')
    print(f'CREATE_DATA: {data}')
    req = requests.post(df_ref+'/'+str(child)+'.json',json=data)
    return req

def put_config(child, data):
    print(f'UPDATE_RATE: {data}')
    req = requests.put(df_ref+'/'+str(child)+'.json',json={'current_rate': data})
    return req

def get_config(child):
    pass

# TODO LAB 1 - Implement the data collection loop in a thread
class DataCollection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # initialize the current_rate value in the cache
        cache.set("current_rate", 1.0)
        # TODO LAB 2 - Put an initial rate in the config stored in the DB
        put_config('config',cache.get("current_rate"))

    def run(self):
        # TODO LAB 1 - Get acceleration data values (x, y and z) from the simulation and print them to the console
        # TODO LAB 2 - Push the data to the real-time database on Firebase
        while(True):
            accel[0] = get_data_from_simulation('accelX')
            accel[1] = get_data_from_simulation('accelY')
            accel[2] = get_data_from_simulation('accelZ')
            if (accel[0]!=None):
                x = { 'data': accel[0],
                      'timestamp': time.time()
                    }
                push_data('accel_x', x)
            if (accel[1]!=None):
                y = { 'data': accel[1],
                      'timestamp': time.time()
                    }   
                push_data('accel_y', y)
            if (accel[2]!=None):
                z = { 'data': accel[2],
                      'timestamp': time.time()
                    }
                push_data('accel_z', z)

# TODO LAB 1 - Implement the UpdateRate resource
class UpdateRate(Resource):
    def put(self,current_rate):
        cache.set("current_rate",current_rate)
        put_config('config',cache.get("current_rate"))
        return {'current_rate': current_rate}


# TODO LAB 1 - Define the API resource routing
api.add_resource(UpdateRate, '/update_rate/<int:current_rate>')

def get_x():
    return accel[0]

def get_y():
    return accel[1]

def get_z():
    return accel[2]

if __name__ == '__main__':
    sim.simxFinish(-1) # just in case, close all opened connections
    clientID=sim.simxStart('127.0.0.1',19997,True,True,5000,5) # Connect to CoppeliaSim
    if clientID!=-1:
        # TODO LAB 1 - Start the data collection as a daemon thread
        d = DataCollection()
        d.daemon = True
        d.start() #start thread
        app.run(debug=True, threaded=True)
    else:
        exit()
