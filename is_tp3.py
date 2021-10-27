from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from flask_caching import Cache
import sim
import time 
import threading
import requests
import paho.mqtt.publish as publish

app = Flask(__name__)
api = Api(app)

# Instantiate the cache
cache = Cache()
cache.init_app(app=app, config={"CACHE_TYPE": "filesystem",'CACHE_DIR': './tmp'})

# global configuration variables
clientID=-1
accel = [0,0,0]

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

def publish_data(number,axis):
    publish.single("python/mqtt/"+axis, number, hostname="localhost")

class DataCollection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # initialize the current_rate value in the cache
        cache.set("current_rate", 1.0)

    def run(self):
        # Get acceleration data values (x, y and z) from the simulation and print them to the console
        while(True):
            accel[0] = get_data_from_simulation('accelX')
            accel[1] = get_data_from_simulation('accelY')
            accel[2] = get_data_from_simulation('accelZ')
            if (accel[0]!=None):
                publish_data(accel[0],'x')
                print(f"Publish to topic-x: {accel[0]}")
            if (accel[1]!=None):
                publish_data(accel[1],'y')
                print(f"Publish to topic-y: {accel[1]}")
            if (accel[2]!=None):
                publish_data(accel[2],'z')
                print(f"Publish to topic-z: {accel[2]}")

# Implement the UpdateRate resource
# class UpdateRate(Resource):
#     def put(self,current_rate):
#         cache.set("current_rate",current_rate)
#         return {'current_rate': current_rate}


# Define the API resource routing
# api.add_resource(UpdateRate, '/update_rate/<int:current_rate>')


if __name__ == '__main__':
    sim.simxFinish(-1) # just in case, close all opened connections
    clientID=sim.simxStart('127.0.0.1',19997,True,True,5000,5) # Connect to CoppeliaSim
    if clientID!=-1:
        # Start the data collection as a daemon thread
        d = DataCollection()
        d.daemon = True
        d.start() #start thread
        app.run(debug=True, threaded=True)
    else:
        exit()
