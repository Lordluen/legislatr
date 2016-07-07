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
#USERNAME = 'lordluen'


def create_database(dbname):
    """
    Will create a new database.
    One of the earlier functions, so it creates it's own connection engine.
    Be cautious, it uses the default user (generally set to 'postgres').

    INPUT:
    dbname = name of database (str)

    OUTPUT: None
    """
    #create a database with name "dbname" using postgres and USERNAME.
    engine = create_engine('postgres://%s@localhost/%s'%(USERNAME,dbname))
    print(engine.url)
    if not database_exists(engine.url):
        create_database(engine.url)
    print(database_exists(engine.url))
    return

def push_to_database(dbname,df_name,df):
    """
    Will save a pandas DataFrame to database. This will overwrite an existing table. Use with caution.

    INPUT:
    dbname = name of database (str)
    df_name = table name in database (str)
    df = pandas DataFrame object to be written to table. (pandas.DataFrame)

    OUTPUT: None
    """
    engine = create_engine('postgres://%s@localhost/%s'%(USERNAME,dbname))
    df.to_sql(df_name,engine,if_exists='replace')
    return

def pull_from_database(dbname,df_name):
    """
    Read in a table from postgres to a pandas dataframe.
    One of the earlier functions, so it creates it's own connection engine.
    Be cautious, it uses the default user (generally set to 'postgres').

    INPUT:
    dbname = name of database (str)
    df_name = table name in database (str)

    OUTPUT:
    df = DataFrame object with table from postgres loaded (pandas.DataFrame)
    """
    #will pull a table from database as a dataFrame.
    engine = create_engine('postgres://%s@localhost/%s'%(USERNAME,dbname))
    df = pd.read_sql_table(df_name,engine)
    return df

def get_engine(dbname,username = USERNAME):
    """
    Returns a postgres connection engine from sqlAlchemy to be used in other functions.

    INPUT:
    dbname = name of database (str)
    username = The username for the postgresql database. Default set to 'postgres'.

    OUTPUT:
    engine = sqlAlchemy engine connecting to postgres database of name dbname.
    """
    #create SQLAlchemy engine.
    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))
    return engine
    
def append_to_database(dbname,df_name,df,engine):
    """
    Will append a table with rows from a pandas DataFrame. This does not overwrite an old table.

    INPUT:
    dbname = name of database (str)
    df_name = table name in database (str)
    df = pandas DataFrame object to be written to table. (pandas.DataFrame)
    engine = SQL connection engine from sqlAlchemy or psycopg2. I used sqlAlchemy with postgresql.

    OUTPUT: None
    """
    df.to_sql(df_name,engine,if_exists='append')
    return

def write_to_database(dbname,df_name,df,engine):
    """
    Will save a pandas DataFrame to database. This will overwrite an existing table. Use with caution.
    dbname = name of database (str)
    df_name = table name in database (str)
    df = pandas DataFrame object to be written to table. (pandas.DataFrame)
    engine = SQL connection engine from sqlAlchemy or psycopg2. I used sqlAlchemy with postgresql.

    OUTPUT: None
    """
    df.to_sql(df_name,engine,if_exists='replace')
    return


