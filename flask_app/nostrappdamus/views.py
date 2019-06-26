from flask import render_template, jsonify, request
import json

from .model.predict import get_recommendations
from .model.get_model import get_items, get_items_map
from nostrappdamus import app


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
    race = args.get('race')
    filterBy = args.get('filterBy')
    model = args.get('model')
    months_range = args.get('months_range')

    # experience type: 0 -> vacation, 1 -> enjoy, 2 -> performance
    # difficulty: 1, 2, 3, 4, 5
    # size: 1, 2, 3, 4, 5
    options = args.get('options')

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

