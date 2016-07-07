"""
Read in vote information from https://www.govtrack.us/data/congress/ (info at
https://www.govtrack.us/developers/data)
    - mynameisfiber (2016/05/11)
"""
import numpy as np
import pandas as pd
import ujson as json
from tqdm import tqdm
from sqlCommands import append_to_database

from dateutil.parser import parse as DateParser
import os


DATADIR = '../Legis_data/votes/'
VOTE_TYPES = {
    "Yea": True,
    "Aye": True,
    "Nay": False,
    "No": False,
    "Not Voting": None,
    "Present": None,
}


def get_votes_files(datadir=DATADIR, start_year=None):
    for congress in tqdm(os.listdir(datadir)):
        if not congress.isnumeric():
            continue
        congress_path = os.path.join(datadir, congress, 'votes/')
        for year in os.listdir(congress_path):
            try:
                if start_year and int(year) < start_year:
                    continue
            except ValueError:
                continue
            year_path = os.path.join(congress_path, year)
            for bill in tqdm(os.listdir(year_path)):
                yield os.path.join(year_path, bill, "data.json")


def parse_votes(fd):
    data = json.load(fd)
    if 'bill' not in data:
        return
    bill_info = {
        "vote_id": data['vote_id'],
        "date": DateParser(data['date']),
        "subject": data.get('subject'),
        "question": data.get('question'),
    }
    bill_info.update({('bill_' + k):v for k,v in data['bill'].items()})
    vote_types = data['votes'].keys()
    if not all(v in VOTE_TYPES for v in vote_types):
        return
    for vote_type in vote_types:
        vote_cast = VOTE_TYPES[vote_type]
        for vote in data['votes'][vote_type]:
            _id = vote["id"]
            vote['vote'] = vote_cast
            vote.update(bill_info)
            yield vote


def read_votes(datadir=DATADIR, start_year=None):
    votes_files = get_votes_files(datadir, start_year)
    for votefile in votes_files:
        with open(votefile) as fd:
            try:
                yield from parse_votes(fd)
            except (KeyError, TypeError) as e:
                pass


def votes(dbname,engine,datadir=DATADIR, start_year=None):
    raw_votes = read_votes(datadir, start_year)
    data = pd.DataFrame.from_dict(raw_votes)
    #for field in ('bill_congress', 'bill_number', 'bill_type', 'display_name',
    #              'first_name', 'id', 'last_name', 'party', 'state', 'vote',
    #              'vote_id'):
    #    data[field] = data[field].astype('category')       
    #append_to_database(dbname,'votes',data,engine)
    print('leaving votes')
    return data


if __name__ == "__main__":
    data = votes(start_year=2008)
