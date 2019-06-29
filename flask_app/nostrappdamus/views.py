from flask import render_template, jsonify, request
import json

from .model.predict import get_recommendations
from .model.get_model import get_items, get_items_map
from nostrappdamus import app

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('activity.log')
handler.setLevel(logging.INFO)

# create a logging format
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/recommend', methods=['POST'])
def get_recommendation():

    args = request.json
    # experience type: 0 -> vacation, 1 -> enjoy, 2 -> performance
    # difficulty: 1, 2, 3, 4, 5
    # size: 1, 2, 3, 4, 5
    options = args.get('options')

    # write to log
    IP1 = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) 
    IP2 = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ["REMOTE_ADDR"]) 
    logger.info(f"({IP1}, {IP2}) -- [{args.get('model')}, {args.get('race')}, {args.get('filterBy')}, {args.get('months_range')}, {options.get('raceExperience')}, {options.get('raceDifficulty')}, {options.get('raceSize')}]")

    # process request
    race = args.get('race')
    filterBy = args.get('filterBy')
    model = args.get('model')
    months_range = args.get('months_range')

    if race:
        if filterBy == 'all':
            # recommendations = get_most_similar_races_to(race)
            recommendations = get_recommendations(race, model_number=model, options=options, months_range=months_range)
        elif filterBy == '70.3':
            # recommendations = get_most_similar_races_to(race, filterBy='is_70.3', valueToMatch=True)
            recommendations = get_recommendations(race, model_number=model, filterBy='is_70.3', valueToMatch=True, 
                                                  options=options, months_range=months_range)
        else:
            # recommendations = get_most_similar_races_to(race, filterBy='is_70.3', valueToMatch=False)
            recommendations = get_recommendations(race, model_number=model, filterBy='is_70.3', valueToMatch=False, 
                                                  options=options, months_range=months_range)

        results = recommendations.to_json(orient='records')

        response = jsonify({ 
          'message': 'Data received.',
          'data': json.loads(results)
        }), 200
    else:
        response = jsonify({ 
          'message': 'Data received.',
          'data': []
        }), 200

    return response


@app.route('/racelist')
def get_races():
    # races_list = list(get_races_list().index)
    races_list = get_items().racename.to_dict()
    response = jsonify({ 
      'message': 'Data received.',
      'data': races_list
    }), 200

    return response

@app.route('/racemap', methods=['POST'])
def get_race_maps():
    race = request.json.get('race')

    maps_data = get_items_map(race or 'france.70.3')

    response = jsonify({ 
      'message': 'Data received.',
      'data': maps_data
    }), 200

    return response

