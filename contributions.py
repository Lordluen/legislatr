"""
Reads data from lobbying contributions into a pandas dataframe.  Data directly
from the following source in it's raw XML format:

http://www.senate.gov/legislative/Public_Disclosure/contributions_download.htm
    - mynameisfiber (2016/05/11)
    - Ethan D. Peck (2016/06/06) (lordluen)
"""
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm
from sqlCommands import append_to_database
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re

from dateutil.parser import parse as DateParser
import os


DATADIR = "../Legis_data/contributions"
FIELD_SPECS={
    'year': int,
    'amount': float,
    'registrantid': int,
    'received': DateParser,
    'contributiondate': DateParser,
    'contributiontype': str,
    'registrantname': str,
    'honoree': str,
}


def _dict_lower_keys(d):
    """
    Turns all keys in dictionary (d) into lowercase.
    """
    return {k.lower():v for k,v in d.items()}

def parse_contribution_filing(fd):
    """
    Takes opened xml file and reads all contribution data in the file. Returns a dataframe with contribution data.
    
    INPUT: fd = opened xml file. (file)
    OUTPUT: alldat = pandas dataframe with contribution data from xml file, fd.
    """
    dom = ET.fromstring(fd.read())
    counter = 0
    data = {}
    data_topush = {}
    alldat = pd.DataFrame()
    #loop over each filing
    for filing in tqdm(dom.findall('.//Filing')):
        #loop over registrant for filing (should only be one).
        for reg in filing.findall('.//Registrant'):
            #loop over each contribution made in the filing.
            for child in filing.findall('.//Contribution'):
                data.clear()
                data_topush.clear()
                #load up the data dictionary with all info.
                data.update(_dict_lower_keys(filing.attrib))
                data.update(_dict_lower_keys(child.attrib))
                data.update(_dict_lower_keys(reg.attrib))
                #pull only the data I care about.
                data_topush = {key:cast(data[key]) for key,cast in FIELD_SPECS.items()}
                #load into a dataframe. this is slow and can be made better if I find the time.
                for key,cast in FIELD_SPECS.items():
                    alldat.loc[counter,key] = cast(data[key])
                counter = counter + 1
    #force ints to be ints.
    alldat['year'] = alldat['year'].astype(int)
    alldat['registrantid'] = alldat['registrantid'].astype(int)
    return alldat
                


def read_contribution_filings(datadir, dbname, engine, start_year=None):
    """
    This will read in and save out contribution data from xml to a sql table.

    INPUT:
    dbname = name of database (str)
    engine = sqlalchemy connector to database.
    datadir = directory where contribution data is located.
    start_year = The year to start pulling contributions from. For ease, all contributions should be read in.
    
    OUTPUT: None
    
    """
    for filename in os.listdir(datadir):#tqdm(os.listdir(datadir)):
        if filename.endswith('.xml'):
            year = int(filename.split('_')[0])
            if start_year and year >= start_year:
                abspath = os.path.join(datadir, filename)
                print(abspath)
                with open(abspath) as fd:
                    try:
                        filedata = parse_contribution_filing(fd) #get contributions from file as pd.df.
                        append_to_database(dbname,'contrib',filedata,engine)
                    except:
                        pass
    return


def contribution_filings(dbname,engine,datadir=DATADIR, start_year=None):
    """
    A calling function that will call necessary functions and print debug statements.
    Function called will read in contributions from files and save them to table 'contrib' in database dbname.
    
    INPUT:
    dbname = name of database (str)
    engine = sqlalchemy connector to database.
    datadir = directory where contribution data is located. Set by default.
    start_year = The year to start pulling contributions from. For ease, all contributions should be read in.
    
    OUTPUT: None
    """
    #new version meant to be used with postgresql.
    print('please print this')
    read_contribution_filings(datadir, dbname, engine, start_year)
    print('leaving contribution_filings')
    return

def pull_contributions(legis,legis_all,engine):
    """
    Will return a dataframe with all contributions to a given legislator
    
    INPUT:
    legis is the legislator dataframe
    legis_all is a dataframe with all legislators.
    engine is a sqlalchemy connector.
    
    OUTPUT:
    finaldf is a pandas dataframe with all contributions for a given legislator.
    """
    #i is the row in question (legislator we care about)
    fname = legis.fname.iloc[0]
    lname = legis.lname.iloc[0]
    olname = lname
    station = legis.station.iloc[0]
    name = legis.qsponsor.iloc[0]
    #clean name for query
    fname = re.sub("'","''",fname)
    lname = re.sub("'","''",lname)
    perfectQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+fname+"%%' AND honoree LIKE '%%"+lname+"%%' AND contributiontype LIKE 'FECA' ;" #definite
    lessQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+lname+"%%' AND contributiontype LIKE 'FECA' ;" #definite + maybe
    perfectdf = pd.read_sql_query(perfectQ,engine)
    lessdf = pd.read_sql_query(lessQ,engine)
    maybedf = pd.concat([perfectdf,lessdf],axis=0).drop_duplicates(keep=False) #maybe

    #finaldf = perfectdf #will concatanate successful matches
    #reduce total number of possible legislators to fuzzy
    fuzz_legis = legis_all[legis_all.lname == olname]['qsponsor'].tolist()

    #print(fuzz_legis)
    matchbool = list()
    matchstr = list()

    #reduce list if it addresses the wrong station
    if station == 'Rep':
        opp_station = 'Sen'
    if station == 'Sen':
        opp_station = 'Rep'
    bools = [not i for i in maybedf.honoree.str.contains(opp_station)] #if it contains opposing station, then not correct.
    maybedf2 = maybedf[bools]
    for c in range(maybedf2.index.size):
        con = maybedf2.honoree.iloc[c]
        match = process.extractOne(con,fuzz_legis)
        if (match[0] ==  name) and match[1] > 55:
            matchbool.append(1)
        else:
            matchbool.append(0)
    matchbool = np.array(matchbool).astype(bool)
    maybedf3 = maybedf2[matchbool]
    finaldf = pd.concat([perfectdf,maybedf3],axis=0)
    return finaldf


if __name__ == "__main__":
    """
    No longer in use.
    """
    contribution_filings()
    print("\nSample result:")
    print(data[data['contributiontype'] == 'FECA'][['honoree', 'amount']] \
            .groupby('honoree') \
            .aggregate(np.sum) \
            .query('amount > 10') \
            .sort('amount'))
