"""
sqlCommands.py
This will contain all of my postgresql python commands for my Insight project.
Create By, Ethan D. Peck
"""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2

USERNAME = 'postgres'


def create_database(dbname):
    #create a database with name "dbname" using postgres ad username.
    #dbname = 'legislatr'
    username = 'postgres'
    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    print(engine.url)
    if not database_exists(engine.url):
        create_database(engine.url)
    print(database_exists(engine.url))
    return

def push_to_database(dbname,df_name,df):
    #will save a dataFrame to database.
    username = 'postgres'
    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    df.to_sql(df_name,engine,if_exists='replace')
    return

def pull_from_database(dbname,df_name):
    #will pull a table from database as a dataFrame.
    username = 'postgres'
    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    df = pd.read_sql_table(df_name,engine)
    return df

def get_engine(dbname,username = USERNAME):
    #create SQLAlchemy engine.
    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    return engine
    
def append_to_database(dbname,df_name,df,engine):
    #will append a dataFrame to a table (df_name) in the postgresql database
    #username = 'postgres'
    #engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    df.to_sql(df_name,engine,if_exists='append')
    return

def write_to_database(dbname,df_name,df,engine):
    #will (over)write a dataFrame to a table (df_name) in the postgresql database
    #username = 'postgres'
    #engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    df.to_sql(df_name,engine,if_exists='replace')
    return


