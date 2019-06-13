from flask import render_template, jsonify, request
import json

from .model.predict import get_most_similar_races_to, get_races_list
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
    race = request.json.get('race')
    filterBy = request.json.get('filterBy')

    if race:
        if filterBy == 'all':
            recommendations = get_most_similar_races_to(race)
        elif filterBy == '70.3':
            recommendations = get_most_similar_races_to(race, filterBy='is_70.3', valueToMatch=True)
        else:
            recommendations = get_most_similar_races_to(race, filterBy='is_70.3', valueToMatch=False)
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
    races_list = get_races_list().racename.to_dict()
    response = jsonify({ 
      'message': 'Data received.',
      'data': races_list
    }), 200

    return response
