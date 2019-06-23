import pandas as pd
import mysql.connector

from config import Cfg as cfg


def get_results_df(df_races=None, anonimize=True):
  cnx = mysql.connector.connect(user=cfg.mysql_user, database=cfg.mysql_db, password=cfg.mysql_pw, ssl_disabled=True)

  query = "SELECT * FROM results;"

  # execute the query and assign it to a pandas dataframe
  df_results = pd.read_sql(query, con=cnx)

  cnx.close()

  print("Number of single results:", len(df_results))
  print("Number of individuals:", len(df_results.athlete.unique()))

  # worldchampionship70.3 and worldchampionship70.3m are the same race
  df_results.loc[df_results.race == "worldchampionship70.3m", 'race'] = 'worldchampionship70.3'

  if type(df_races) != type(None):
      # keep only results of non discontinued races
      df_results = df_results[df_results['race'].isin(df_races.index)]

  # remove world championship races since we cannot really recommend it
  df_results = df_results[~df_results['race'].str.contains('worldchampionship')]

  # extract gender from division
  df_results['gender'] = df_results['division'].apply(lambda x: x[0])

  # convert date to datetime
  df_results['date'] = pd.to_datetime(df_results['date'])

  # str to int
  df_results['year'] = df_results['year'].apply(int)

  # keep only results from after 2015
  df_results = df_results.loc[df_results['year'] >= 2015]

  # # discard pro athletes
  # df_results = df_results.loc[df_results.division.str.contains("PRO") == False]

  # Add gender
  df_results['gender'] = None
  df_results.loc[df_results['division'].str.contains("M"), 'gender'] = "M"
  df_results.loc[df_results['division'].str.contains("F"), 'gender'] = "F"

  if anonimize:
      user_hash = {}

      for i,user in enumerate(df_results.athlete.unique()):
          user_hash[user] = f'u{i}'
      df_results.loc[:, 'athlete'] = df_results.athlete.map(lambda x: user_hash[x])


  print("Number of remaining single results:", len(df_results))
  print("Number of remaining individuals:", len(df_results.athlete.unique()))
  print("Number of races in results df:", len(df_results.race.unique()))

  return df_results


def get_athletes_races_count(df_results):

    # total number of races per athlete
    athletes_count_races = (df_results.groupby('athlete')['division']
         .size()
         .reset_index()
         .rename(columns={'division': 'n_races'})
    )

    # total number of different races per athlete
    athletes_count_diff_races = (df_results
         .groupby(['athlete', 'race'])
         .size()
         .reset_index()
         .groupby('athlete')
         .size()
         .reset_index()
         .rename(columns={0: 'n_different_races'})
    )

    # merge the two so we can filter from that
    athlete_habits = athletes_count_diff_races.merge(athletes_count_races, left_on="athlete", right_on="athlete", how="left")

    return athlete_habits

