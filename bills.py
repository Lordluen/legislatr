"""
Read in bill information from https://www.govtrack.us/data/congress/ (info at https://www.govtrack.us/developers/data)
Written By,
Ethan D. Peck
"""
import numpy as np
import pandas as pd
import ujson as json
from tqdm import tqdm
from sqlCommands import append_to_database

from dateutil.parser import parse as DateParser
import os

DATADIR = '../Legis_data/votes/'
CURR_CONGRESS = 114
RESULTMAP = {
    "INTRODUCED":2,
    "REFERRED":2,
    "REPORTED":2,
    "PROV_KILL:SUSPENSIONFAILED":0,
    "PROV_KILL:CLOTUREFAILED":0,
    "FAIL:ORIGINATING:HOUSE":0,
    "FAIL:ORIGINATING:SENATE":0,
    "PASSED:SIMPLERES":1,
    "PASSED:CONSTAMEND":1,
    "PASS_OVER:HOUSE":2,
    "PASS_OVER:SENATE":2,
    "PASSED:CONCURRENTRES":1,
    "FAIL:SECOND:HOUSE":0,
    "FAIL:SECOND:SENATE":0,
    "PASS_BACK:HOUSE":2,
    "PASS_BACK:SENATE":2,
    "PROV_KILL:PINGPONGFAIL":0,
    "PASSED:BILL":1,
    "CONFERENCE:PASSED:HOUSE":2,
    "CONFERENCE:PASSED:SENATE":2,
    "ENACTED:SIGNED":1,
    "PROV_KILL:VETO":1,
    "VETOED:POCKET":1,
    "VETOED:OVERRIDE_FAIL_ORIGINATING:HOUSE":1,
    "VETOED:OVERRIDE_FAIL_ORIGINATING:SENATE":1,
    "VETOED:OVERRIDE_PASS_OVER:HOUSE":1,
    "VETOED:OVERRIDE_PASS_OVER:SENATE":1,
    "VETOED:OVERRIDE_FAIL_SECOND:HOUSE":1,
    "VETOED:OVERRIDE_FAIL_SECOND:SENATE":1,
    "ENACTED:VETO_OVERRIDE":1,
    "ENACTED:TENDAYRULE":1
}


def get_bills_files(datadir=DATADIR):
    """
    Iterator function that yields the next directory for a valid bill.
    """
    for congress in os.listdir(datadir):
        if not congress.isnumeric():
            continue #only want actual session info.
        if int(congress) < 111:
            continue
        congress_path = os.path.join(datadir, congress, 'bills/')
        try: #will fail if bills was not in the congress path (so old sessions are skipped).
            for room_type in os.listdir(congress_path):
                if (room_type == 'hr') | (room_type == 's'):
                    bills_path = os.path.join(congress_path,room_type) #bills because this is all of the bills.
                    for bill in tqdm(os.listdir(bills_path)):
                        bill_file = os.path.join(bills_path,bill,"data.json")
                        yield bill_file
                else:
                    continue
        except:
            continue #early sessions only have vote info, not actual bills.
            
def parse_bills(bill_file, dbname, engine):
    """
    Parses a given bill and stores the information from it into a database.
    
    INPUT:
    bill_file = opened file with bill information (file)
    dbname = The name of the database. (str)
    engine = connection engine, such as from from sqlalchemy.
    
    OUTPUT: None
    """
    
    #read in data
    data = json.load(bill_file)
    #pull out info from file.
    subjects=list(data['subjects'])
    top_subject=data['subjects_top_term']
    bill_type = data['bill_type']
    bill_number = data['number']
    title = data['short_title']
    ltitle = data['official_title']
    amends = data['amendments']
    congress = int(data['congress'])
    num_amends = len(amends)
    status = data['status']
    intro_date = DateParser(data['introduced_at'])
    active = data['history']['active']
    allcoms = data['committees']
    #get all committees on the bill.
    coms = list()
    for c in allcoms:
        coms.append(c['committee_id'])
    final_coms = [np.unique(coms).tolist()]
    #get the date the bill ended (will not exist if it died from end of session).    
    try:
        final_date = DateParser((data['summary'])['date'])
    except:
        final_date = None
    #get sponsors on the bill.    
    tsponsor = data['sponsor']
    if tsponsor['type'] == 'person': #lets only use bills from people, not committees. Since funding would be hard to trace otherwise.
        sponsor = [tsponsor['title'],tsponsor['name'],tsponsor['state']]
        tcosponsors = data['cosponsors']
        cosponsors = list()
        if len(tcosponsors) > 0:
            for co in tcosponsors:
                cosponsors.append([co['title'],co['name'],co['state']])
    #put the info into a dataframe.
    foo = pd.DataFrame()
    foo['subjects'] = [subjects]
    foo['top_subject'] = top_subject
    foo['bill_type'] = bill_type
    foo['bill_number'] = bill_number
    foo['status'] = status  
    foo['result'] = foo['status'].map(RESULTMAP) #0 = failed, 1 = passed, 2 = pending
    foo['sponsor'] = [sponsor]
    foo['cosponsors'] = [cosponsors]
    foo['intro_date'] = intro_date
    foo['final_date'] = final_date
    foo['title'] = title
    foo['num_amends'] = num_amends
    foo['otitle'] = ltitle
    foo['committees'] = final_coms
    foo['congress'] = congress
    #if a bill is active (True) assign it a value of 1, else 0.
    if active == True:
        foo['active'] = [1]
    if active == False:
        foo['active'] = [0]
    #create a final result field for use in the final model. If it is not officially dead (value of 2),
    #but it is from an older congress, then it is dead, so reset value to 0.
    foo['final_result'] = foo['result'] 
    if (foo['result'].iloc[0] == 2) and (congress < CURR_CONGRESS):
        foo['final_result'] = [0]
    
    #append to table allbills4. Older versions of the code had allbills through allbills3.
    append_to_database(dbname,'allbills4',foo,engine)

    return

def read_bills(dbname,engine,datadir=DATADIR, start_year=None):
    """
    Function that loops over all bill files and sends to parser for saving to the database.
    INPUT:
    dbname = The name of the database. (str)
    engine = connection engine, such as from from sqlalchemy.
    datadir = location of bill data. This is already set by default.
    start_year = The beginning year to pull bills from through present. (int)
    
    OUTPUT: None
    """
    
    #this will read in bills
    #votes_files = get_votes_files(datadir, start_year)
    bills_files = get_bills_files(datadir)
    for billfile in bills_files:
    #only want bills that get to a vote. So first find the vote file to get a bill number.
        with open(billfile) as fd:
            try:
                parse_bills(fd,dbname,engine) #parse bill using info from prev line.
            except (KeyError, TypeError) as e:
                pass
    return

def bills( dbname, engine, datadir=DATADIR, start_year=None ):
    """
    This function will call all other functions necessary to load in bills to a database.
    INPUT: 
    dbname = The name of the database. (str)
    engine = connection engine, such as from from sqlalchemy.
    datadir = location of bill data. This is already set by default.
    start_year = The beginning year to pull bills from through present. (int)
    
    OUTPUT: None
    """
    
    #this will read in bills
    #raw_bills = read_bills( datadir, start_year )
    read_bills( dbname,engine,datadir, start_year )
    #data = pd.DataFrame.from_dict( raw_bills )
    #append_to_database(dbname,'bills',data,engine)
    print('leaving bills')
    return
