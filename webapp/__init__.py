import os
from flask import Flask, render_template, request
import pickle
import numpy as np
import json
import datetime

class Predictor:

    def __init__(self):
        self.model = None
        self.encoder = None
        self.scaler = None
        self.cwd = os.path.dirname(os.path.abspath(__file__))
    
    def _add_long_lat(self, airport_code):
        LONG_LAT_MAP = os.path.join(self.cwd, 'airport_lat_long.v2.txt')
        with open(LONG_LAT_MAP, 'r') as file:
            mp = json.load(file)
        try:
            airport = mp[airport_code]
            lat, long = airport['lat'], airport['long']
            return lat, long
        except Exception as e:
            return None, None

    
    def load_model(self, model_name = 'logistic_regression.pkl'):
        # cwd = os.path.dirname(os.path.abspath(__file__))
        LOG_REGRESSION_PATH = os.path.join(self.cwd, model_name) 
        LABEL_ENCODER = os.path.join(self.cwd, 'label_encoder.pkl') 
        SCALER = os.path.join(self.cwd, 'min_max_scaler.pkl') 

        with open(LOG_REGRESSION_PATH, 'rb') as file:
            self.model = pickle.load(file)
        with open(LABEL_ENCODER, 'rb') as file:
            self.encoder = pickle.load(file)
        with open(SCALER, 'rb') as file:
            self.scaler = pickle.load(file)
    
    def forward(self, **kwargs):
        month = kwargs['month']
        day_of_month =  kwargs['day_of_month']
        day_of_week =   kwargs['day_of_week']
        dep_time =      kwargs['dep_time']
        arr_time =      kwargs['arr_time']
        carrier =       kwargs['carrier']
        #label encode carrier
        carrier_number = self.encoder.transform([carrier])
        carrier_number = carrier_number[0]
        elapsed_time = kwargs['elapsed_time']
        distance =     kwargs['distance']
        origin_airport = kwargs['origin_airport']
        dest_airport = kwargs['dest_airport']
        #transform airpot to origin lat and long coord 
        origin_lat, origin_long = self._add_long_lat(origin_airport)
        dest_lat, dest_long = self._add_long_lat(dest_airport)

        datapoint = [
            month,
            day_of_month,
            day_of_week,
            dep_time,
            arr_time,
            carrier_number,
            elapsed_time,
            distance,
            origin_lat,
            origin_long,
            dest_lat,
            dest_long
        ]

        print('data point = ', datapoint)

        datapoint = np.array(datapoint)
        datapoint = self.scaler.transform([datapoint])
        Y  =  self.model.predict_proba(datapoint)
        return Y
    
    def __str__(self):
        print(type(self.model))
        print(type(self.encoder))
        print(type(self.scaler))
        return ''


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    try:
        predictor = Predictor()
        predictor.load_model()
        print("SUCESSFULLY LOADED MODEL")
        print("=" * 20)
        print("PREDICTOR INFOR")
        print(predictor)
        print("=" * 20)

        #print test
        # probs = predictor.forward(month = 1, day_of_month = 3, day_of_week = 3,
        # dep_time = 1955, arr_time = 2215, carrier = 'CO', elapsed_time = 150, 
        # distance= 810, origin_airport = 'IAD', dest_airport= 'TPA')
        # print('probs = ', probs)

    except Exception as e:
        print("FAILED TO LOAD MODEL")
        print(e)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def hello():
        return render_template("index.html",name = "james")
    
    @app.route('/submit_data', methods = ['POST'])
    def submit_data():
        try:
            form = request.form 
            carrier = form['airline']

            date = form['date']
    
            #Transforming the user input data into this data to be used by the model
            # date = '2023-12-07'
            year, month, day_of_month = map(lambda x: int(x), date.split('-'))
            dateobj = datetime.date(year, month, day_of_month)
            day_of_week = dateobj.weekday()

            #Transform dep-time and arr_time
            dep_time = form['dep_time']
            arr_time = form['arr_time']
            #parse data
            #get elapsed time
            dep_h, dep_m = dep_time.split(':')
            dep_total = int(dep_h) * 60 + int(dep_m)
            arr_h, arr_m = arr_time.split(':')
            arr_total = int(arr_h) * 60 + int(arr_m)

            elapsed_time = abs(arr_total - dep_total)

            #Convert dep and arrival time from string hh:mm to a number hhmm
            dep_time = int(dep_h) * 10 + int(dep_m)
            arr_time = int(arr_h) * 10 + int(dep_m)

            #load origin and dest aiport
            origin_airport = form['origin_airport']
            #
            dest_airport = form['dest_airport']

            distance = form['distance']

            datapoint = {
                'month': month, 
                'day_of_month': day_of_month, 
                'day_of_week': day_of_week, 
                'dep_time': dep_time, 
                'arr_time': arr_time,
                'carrier': carrier, 
                'elapsed_time': elapsed_time, 
                'distance': distance, 
                'origin_airport': origin_airport, 
                'dest_airport': dest_airport
                }
            
            print("submit datapoint = ", datapoint)
            probs = predictor.forward(**datapoint)
            print('props = ', probs)
            nondelayed_prob, delayed_prob = probs[0]
            delayed_prob *= 100
            delayed_prob = f"{delayed_prob:.1f}"
            print(delayed_prob)

            return render_template("index.html",name = "Submitted A Form", delayed_prob = delayed_prob)
        except Exception as e:
            print(e)
            return f'<h1>{e}</h1>'

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get('PORT', 3030))
    app.run(debug=True, host='0.0.0.0', port=port)
