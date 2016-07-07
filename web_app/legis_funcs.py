#legis_funcs.py
#This will contain all of the functions used by the legislatr web-app.
#Created By, Ethan D. Peck

import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from sklearn import linear_model
from sklearn.ensemble import RandomForestClassifier
import pickle
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import numpy as np

def runModel(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status','final_result','congress'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    result = model.predict(X)
    return result

def modelConf(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status','final_result','congress'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    P = model.predict_proba(X)
    #print(type(P[0]))
    #print(P[0][1])
    #print(P)
    #Pr = max(P[0])*100. #convert to percent
    Pr = P[0][1]*100.
    return Pr

def getBill(bill_type,bill_number,congress,engine):
    bill = retrieveFeatures(bill_type,bill_number,congress,engine)
    return bill 

def getResult(model,bill_type,bill_number,congress,engine):
    bill = retrieveFeatures(bill_type,bill_number,congress,engine)
    output = np.zeros((2))
    output[0] = runModel(model,bill)
    output[1] = modelConf(model,bill)
    return output

def retrieveFeatures(bill_type,bill_number,congress,engine):
    #pull a bill's features from postgresql server
    #query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"';"
    #query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' LIMIT 1;"
    query = "SELECT * FROM features_subs WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_subs = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    query = "SELECT * FROM features_legis WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_legis = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    query = "SELECT * FROM features_comms WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_comms = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    #fuse them
    bill = pd.concat([bill_subs,bill_legis.drop(['bill_number','bill_type','index','result','status','final_result','num_amends','congress'],axis=1),
                     bill_comms.drop(['bill_number','bill_type','index','result','status','final_result','num_amends','congress'],axis=1)],axis=1)
    return bill

def initModel(mtype):
    #load model
    #if mtype == 'logreg':
    #    model_file = './legislatr/static/logreg_model_subjects.pkl' #logistic regression
    if mtype == 'forest':
        model_file = './legislatr/static/random_forest_model_subs_legis_comms.pkl' #random forest
    mfile = open(model_file,'rb')
    model = pickle.load(mfile)
    mfile.close()
    return model

def pull_contributions(legis,legis_all,engine):
    #will return a datafram with all contributions to a given legislator
    #legis is the legislator dataframe
    #i is the row in question (legislator we care about)
    fname = legis.fname.iloc[0]
    lname = legis.lname.iloc[0]
    station = legis.station.iloc[0]
    name = legis.qsponsor.iloc[0]
    #clean name for query
    fname = re.sub("'","''",fname)
    lname = re.sub("'","''",lname)
    perfectQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+fname+"%%' AND honoree LIKE '%%"+lname+"%%' AND contributiontype LIKE 'FECA' ;" #definite
    lessQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+lname+"%%';" #definite + maybe
    perfectdf = pd.read_sql_query(perfectQ,engine)
    lessdf = pd.read_sql_query(lessQ,engine)
    maybedf = pd.concat([perfectdf,lessdf],axis=0).drop_duplicates(keep=False) #maybe

    finaldf = perfectdf #will concatanate successful matches
    #reduce total number of possible legislators to fuzzy
    fuzz_legis = legis_all[legis_all.lname == lname]['qsponsor'].tolist()

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
    #maybedf2
    for c in range(maybedf2.index.size):
        con = maybedf2.honoree.iloc[c]
        match = process.extractOne(con,fuzz_legis)
        if (match[0] ==  name) and match[1] > 55:
            matchbool.append(1)
        else:
            matchbool.append(0)
    matchbool = np.array(matchbool).astype(bool)
    maybedf3 = maybedf2[matchbool]
    return maybedf3

def retrieveTitle(bill_type,bill_number,congress,engine):
    query = "SELECT otitle FROM bill_info WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    otitle = pd.read_sql_query(query,engine)["otitle"].iloc[0]
    return otitle

def retrieveFunding(bill_type,bill_number,congress,engine):
    
    legis = pd.read_sql_table('sponsor_list_det',engine)
    
    #load bill
    query = "SELECT * FROM features_legis WHERE bill_type LIKE '"+bill_type+"' AND bill_number 	LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_legis = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the 	most recent one.
    #drop useless columns.
    bill_legis = bill_legis.drop	(['bill_type','bill_number','congress','num_amends','index','status','result','final_result'],1)
    #read in legislator info
    legis = pd.read_sql_table('sponsor_list_det',engine)
	
    cols = bill_legis.columns.tolist()
    mat = bill_legis.as_matrix().flatten().tolist()
    
    #list of legislators on bill
    legislators = list()
    for leg in range(0,len(cols)):
        if mat[leg] == 1:
            legislators.append(cols[leg])
            

    legis_funds = list() #will be a list to hold the dataframes of contributions for each legislator
    legis_names = list()
    for leg in legislators:
        #get index of legislator
        legis_ind = legis[legis.sponsor == leg].index[0]
        legis_names.append(legis[legis.sponsor == leg]['qsponsor'].iloc[0])
        #generate tableid
        tableid = 'legis'+str(legis_ind)
        #read in the contribution table for this legislator and append to list.
        legis_funds.append(pd.read_sql_table(tableid,engine))

    #deal with case of only one legislator.
    if len(legis_names) == 1: 
        onlyFund = legis_funds[0]
        u_shared_rids = np.unique(onlyFund.rid)
        u_shared_names = list()
        for rid in u_shared_rids:
            u_shared_names.append(onlyFund[onlyFund.rid==rid]['name'].iloc[0])
    else:
        #now need to get shared contributors. Do this by concatinating rid's into a big list and keeping only ones that are duplicates.
        #loop through and make a new dataframe with just the amount, rid, and name.
        all_dfs = pd.DataFrame()
        for df in legis_funds:
            all_dfs = pd.concat([all_dfs,df[['amount','name','rid']]],axis=0)
    
        #get duplicate (shared) contributors based on rid
        duplicates = all_dfs[all_dfs.duplicated(subset='rid',keep=False)]
        #get unique rid's of shared contributors.
        u_shared_rids = np.unique(duplicates['rid'])
        #get the names of the unique rids
        u_shared_names = list()
        for rid in u_shared_rids:
            u_shared_names.append(duplicates[duplicates.rid==rid]['name'].iloc[0])
    
    #now I need to calculate influence each rid had on a legislator. So first find intersection of each legislator with unique ids
    shared_funds = list()
    for df in legis_funds:
        shared_contribs = df[df['rid'].isin(u_shared_rids)]
        #get total amount of money in shared_contribs
        total_contribs = sum(shared_contribs.amount.tolist())
        #create a new column in shared contribs with influence (ratio of money to total money).
        shared_contribs['influence'] = (shared_contribs.amount/total_contribs)*100.
        shared_funds.append(shared_contribs)

    #this is the slowest step....
    #calculate top 10 contributors based on influence.
    total_inf = np.zeros(len(u_shared_rids))
    total_money = np.zeros(len(u_shared_rids))

    all_df = pd.concat(shared_funds)
    for i in range(0,len(u_shared_rids)):
        rid = u_shared_rids[i]
        match = all_df[all_df.rid == rid]
        total_inf[i] = total_inf[i]+sum(match['influence'])
        total_money[i] = total_money[i]+sum(match['amount'])
    avg_inf = total_inf/len(shared_funds)
    avg_money = total_money/len(shared_funds)
    
    #zip together u_shared_rids, u_shared_names, total_inf, total_money
    shared_con_zip = list(zip(u_shared_rids.tolist(),u_shared_names,avg_inf.tolist(),avg_money.tolist()))
    #sort based on influence
    shared_con_zip = sorted(shared_con_zip, key=lambda tup: tup[2], reverse=True)

    return (shared_con_zip, shared_funds, legis_names) #(totals, individual df's, legislator names that go with the individual dfs)

def makeBarPlotFile(contrib_tup,rank) :
    #plot the money distribution to individual senators by the largest contributor
    rid = contrib_tup[0][rank][0]
    #output to intermediate file
    funds = list() #money
    inf = list() #influence
    legis = list()  #name
    count = 0
    for j in contrib_tup[1]:
        legis.append(contrib_tup[2][count])
        count = count + 1
        match = j[j.rid == rid]
        if len(match)>0:
            funds.append(match['amount'].iloc[0])
            inf.append(match['influence'].iloc[0])
        else:
            funds.append(0.)
            inf.append(0.)

    with open("legislatr/static/data.tsv", "w") as record_file:
        record_file.write("Legislator\tContribution\tInfluence\n")
        for i in range(0,len(legis)):
            record_file.write(str(legis[i])+"\t"+str(funds[i])+"\t"+str(round(inf[i],2))+"\n")
    return

def get_bills_list(bill_type,congress,engine) :
    query = "SELECT bill_number FROM bill_info WHERE bill_type LIKE '"+bill_type+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_numbers = pd.read_sql_query(query,engine)["bill_number"].tolist()
    return bill_numbers



#def get_query_matches(bills_df, query, max_n_results, engine):
def get_query_matches(query, engine):
    #self is an object.

    to_query = query.lower().split()

    sql_query = "SELECT congress, bill_type, bill_number FROM bill_info WHERE "
    for q in range(0,len(to_query)):
        sql_query = sql_query + "(LOWER(otitle) LIKE '%%"+to_query[q]+"%%' OR LOWER(title) LIKE '%%"+to_query[q]+"%%') AND "
    sql_query = sql_query[:-4]+";"
    print(sql_query)
    results_df = pd.read_sql_query(sql_query, engine)
    results_df['bill_number'] = results_df['bill_number'].astype(str)
    results_df['congress'] = results_df['congress'].astype(str)
    return results_df

    #results is list of indices corresponding to rows in the dataframe, laptops.
    #apply 
    #title is the name of the laptop
    #reviews is the number of reviews for the laptop. * by reviews is for choosing an order. #maybe rank on age of bill.
    #DF.apply applies the function to every row and outputs as a list.
    #results = np.argsort(
    #    self.laptops.apply(
    #        lambda x: -int(all([word in str(x.title).lower() for word in query.lower().split()])) * x.reviews,axis=1))


    #take query words and split
    #if len(results) > max_n_results:  #max_n_results is the maximum number of results desired on a page.
    #    results = results[:self.max_n_results]
    #asins = [self.laptops['asin'].iloc[result] for result in results]  #laptops is a DF #asin is a column that corresponds to item number/identifier.
    #return asins


    
