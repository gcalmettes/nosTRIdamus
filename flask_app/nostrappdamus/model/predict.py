import numpy as np
import pandas as pd

from .get_model import get_items, get_model

# Dictionary of possible models
models = {
  0: 'ALS',
  1: 'KNN_Content'
}

items = get_items()
# will be used to check if we need to load another model in memory
current_model_number = 0
current_model = None


def get_recommendations(raceId, model_number=0, filterBy=False, valueToMatch=False, options={}):
    global current_model, current_model_number

    if (current_model_number == model_number) and (type(current_model) != type(None)):
        # model has already been loaded and we use the same
        return current_model.recommend(raceId, n=10, filterByField=filterBy, valueToMatch=valueToMatch, options=options)
    else:
        # load new model
        current_model_number = model_number
        current_model = get_model(models[int(model_number)])
        print(f"The model {model_number} ({current_model.name}) has been loaded")
        return current_model.recommend(raceId, n=10, filterByField=filterBy, valueToMatch=valueToMatch, options=options)
