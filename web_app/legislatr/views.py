from flask import render_template, request
from legislatr import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
import sqlCommands
import legis_funcs
from random import randint
import pickle

dbname = 'legislatr'
db = sqlCommands.get_engine(dbname)

@app.route('/')
@app.route('/index')
@app.route('/input')
def legislatr_input():
    json_name = str(randint(100,199)) #assign user id.
    return render_template("input.html",data_file=json_name)

@app.route('/input2')
def legislatr_input2():
    congress = request.args.get('congress')
    data = {}
    data['congress'] = congress
    #write data to pickle.
    json_name = request.args.get('data_file')
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        foo = pickle.dump(data,fp)
    return render_template("input2.html",congress=congress,data_file=json_name)

@app.route('/input3')
def legislatr_input3():
    bill_type = request.args.get('bill_type')
    congress = request.args.get('congress')
    json_name = request.args.get('data_file')
    #load data
    with open('legislatr/static/'+json_name+'.p','rb') as fp:
        data = pickle.load(fp)
    data['bill_type'] = bill_type
    data['congress'] = congress
    bill_list = list(map(int,legis_funcs.get_bills_list(bill_type,congress,db)))
    bill_list.sort()
    bill_list = list(map(str,bill_list))
    data['bill_list'] = bill_list
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("input3.html", congress=congress, bill_type=bill_type, bill_list=bill_list,data_file=json_name)

@app.route('/input4')
def legislatr_input4():
    #read data
    json_name = request.args.get('data_file')
    with open('legislatr/static/'+json_name+'.p','rb') as fp:
        data = pickle.load(fp)
    bill_type = data['bill_type']
    congress = data['congress']
    bill_list = data['bill_list']
    bill_number = request.args.get('bill_number')
    data['bill_number'] = bill_number
    title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    data['title'] = title
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("input4.html", congress=congress, bill_type=bill_type, bill_list=bill_list, bill_title=title, bill_number=bill_number,data_file=json_name)

@app.route('/inputSearch')
def legislatr_inputSearch():
    query = request.args.get('query')
    query_db = legis_funcs.get_query_matches(query,db)
    json_name = request.args.get('data_file')
    data = {}
    data["query_db"] = query_db
    options = query_db["congress"].str.cat(query_db["bill_type"],sep=' : ').str.cat(query_db["bill_number"],sep=' : ').tolist()
    data["options"] = options
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("inputSearch.html", bill_options = options, data_file=json_name)

@app.route('/inputSearch2')
def legislatr_inputSearch2():
    ind = int(request.args.get('user_choice'))
    json_name = request.args.get('data_file')
    with open('legislatr/static/'+json_name+'.p','rb') as fp:
        data = pickle.load(fp)
    options = data["options"]
    option = options[ind]
    query_db = data["query_db"]
    congress = query_db["congress"].iloc[ind]
    bill_type = query_db["bill_type"].iloc[ind]
    bill_number = query_db["bill_number"].iloc[ind]
    title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    data['title'] = title
    data['bill_type'] = bill_type
    data['bill_number'] = bill_number
    data['congress'] = congress
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("inputSearch2.html", bill_choice=ind, congress=congress, bill_type=bill_type,bill_number=bill_number,bill_title=title,bill_options=options,data_file=json_name)


@app.route('/about')
def legislatr_about():
    return render_template("about.html")

@app.route('/sample')
def legislatr_sample():
    json_name = request.args.get('data_file')
    data = {}
    bill_type = request.args.get('bill_type')
    congress = request.args.get('congress')
    bill_number = request.args.get('bill_number')
    title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    data['title'] = title
    data['bill_type'] = bill_type
    data['bill_number'] = bill_number
    data['congress'] = congress

    model = legis_funcs.initModel('forest')
    bill = legis_funcs.getBill(bill_type,bill_number,congress,db)
    result = legis_funcs.runModel(model,bill)
    if result[0] == 1:
        the_result = "PASS"
    if result[0] == 0:
        the_result = "FAIL"
    data['the_result'] = the_result
    the_confidence = legis_funcs.modelConf(model,bill)

    data['the_confidence'] = the_confidence
    if the_result == "PASS":
        img_file = 'glyphicon-ok'
        img_color = 'green'
    if the_result == "FAIL":
        img_file = 'glyphicon-remove'
        img_color = 'red'
    data['img_file'] = img_file
    data['img_color'] = img_color

    funding_tup = legis_funcs.retrieveFunding(bill_type,bill_number,congress,db)

    data['funding_tup'] = funding_tup
    legis_funcs.makeBarPlotFile(funding_tup,0) #for now just do the top ranked funder (rank = 0)
    top_ten_funders = list()
    for x in range(0,10):
        top_ten_funders.append(funding_tup[0][x][1]) #the names of the top 10 contributors.
    data['top_ten_funders'] = top_ten_funders
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("output.html",the_result = the_result,
        the_confidence = int(round(the_confidence)),
        funders = top_ten_funders,
        img_file = img_file, img_color = img_color,
        bill_title = title,
        bill_type=bill_type, bill_number=bill_number, congress=congress, data_file=json_name)

@app.route('/output')
def legislatr_output():
    json_name = request.args.get('data_file')
    with open('legislatr/static/'+json_name+'.p','rb') as fp:
        data = pickle.load(fp)
    bill_type = data['bill_type']
    congress = data['congress']
    bill_number = data['bill_number']

    model = legis_funcs.initModel('forest')
    #retrieve the bill information
    bill = legis_funcs.getBill(bill_type,bill_number,congress,db)
    result = legis_funcs.runModel(model,bill)
    if result[0] == 1:
        the_result = "PASS"
    if result[0] == 0:
        the_result = "FAIL"
    data['the_result'] = the_result
    the_confidence = legis_funcs.modelConf(model,bill)
    data['the_confidence'] = the_confidence
    if the_result == "PASS":
        img_file = 'glyphicon-ok'
        img_color = 'green'
    if the_result == "FAIL":
        img_file = 'glyphicon-remove'
        img_color = 'red'
    data['img_file'] = img_file
    data['img_color'] = img_color
    title = data['title']
    funding_tup = legis_funcs.retrieveFunding(bill_type,bill_number,congress,db)
    data['funding_tup'] = funding_tup
    legis_funcs.makeBarPlotFile(funding_tup,0) #for now just do the top ranked funder (rank = 0)
    top_ten_funders = list()
    for x in range(0,10):
        top_ten_funders.append(funding_tup[0][x][1]) #the names of the top 10 contributors.
    data['top_ten_funders'] = top_ten_funders
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("output.html",the_result = the_result,
        the_confidence = int(round(the_confidence)),
        funders = top_ten_funders,
        img_file = img_file, img_color = img_color,
        bill_title = title,
        bill_type=bill_type, bill_number=bill_number, congress=congress, data_file=json_name)

@app.route('/output2')
def legislatr_output2():
    json_name = request.args.get('data_file')
    with open('legislatr/static/'+json_name+'.p','rb') as fp:
        data = pickle.load(fp)
    bill_type = data['bill_type']
    bill_number = data['bill_number']
    congress = data['congress']
    img_file = data['img_file']
    img_color = data['img_color']
    the_confidence = data['the_confidence']
    the_result = data['the_result']
    top_ten_funders = data['top_ten_funders']
    funding_tup = data['funding_tup']
    title = data['title']
    funder = int(request.args.get('contributor'))
    legis_funcs.makeBarPlotFile(funding_tup,funder)
    with open('legislatr/static/'+json_name+'.p','wb') as fp:
        pickle.dump(data,fp)
    return render_template("output2.html",the_result=the_result,
        the_confidence = int(round(the_confidence)),
        funders = top_ten_funders,
        fund = funder,
        img_file = img_file, img_color= img_color,
        bill_title = title,
        bill_type=bill_type, bill_number=bill_number,congress=congress,data_file=json_name)
