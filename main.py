"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - In the session object, date or datetimes are represented as
   ISO format strings in UTC.  Unless otherwise specified, this
   is the format passed around internally. Note that ordering
   of ISO format strings is consistent with date/time order
   - User input/output is in local (to the server) time
   - Database representation is as MongoDB 'Date' objects
   Note that this means the database may store a date before or after
   the date specified and viewed by the user, because 'today' in
   Greenwich may not be 'today' here. 
"""

import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we may still need time
from dateutil import tz  # For interpreting local times

# Mongo database
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

###
# Globals
###
import CONFIG

app = flask.Flask(__name__)

try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated
    #collection = collection.find().sort( { date: 1 } )
except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

import uuid
app.secret_key = str(uuid.uuid4())

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  flask.session['memos'] = get_memos()
  for memo in flask.session['memos']:
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')

@app.route("/_test")
def testing():
    app.logger.debug("Got a JSON request");
    date = request.args.get('date',0,type=str)
    base = arrow.get(date,'MM/DD/YYYY')
    base = base.timestamp
    memo = request.args.get('memo', 1, type=str)
    record = {'type': 'dated_memo', 'date':base, 'text': memo}
    d = {'date': base, 'memo': memo}
    collection.insert(record)
    d = json.dumps(d)
    return jsonify(result = d)

@app.route("/_delId")
def del_memo():
    app.logger.debug("Got a JSON request");
    objId = request.args.get('objId',0,type=str)
    d = {'objId': objId}
    #x = ObjectId(objId)
    collection.remove({"_id": ObjectId(objId)});
    d = json.dumps(d)
    return jsonify(result = d)


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################

# NOT TESTED with this application; may need revision 
#@app.template_filter( 'fmtdate' )
# def format_arrow_date( date ):
#     try: 
#         normal = arrow.get( date )
#         return normal.to('local').format("ddd MM/DD/YYYY")
#     except:
#         return "(bad date)"

@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    try:
        then = arrow.get(date).to('local')
        now = arrow.utcnow().to('local')
        if then.date() == now.date():
            human = "Today"
        else: 
            human = then.humanize(now)
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    #tempCollection = collection.find().sort( { date: 1 } )
    for record in collection.find( { "type": "dated_memo" } ).sort("date",1):
    #for record in collection.find().sort( { date: -1 } ):
        record['date'] = arrow.get(record['date']).isoformat()
        try:
            record['_id'] = str(record['_id'])
        except:
            del record['_id']
        records.append(record)
    return records 


# def put_memo(dt, mem):
#     """
#     Place memo into database
#     Args:
#        dt: Datetime (arrow) object
#        mem: Text of memo
#     NOT TESTED YET
#     """
#     record = { "type": "dated_memo", 
#                "date": dt.to('utc').naive,
#                "text": mem
#             }
#     collection.insert(record)
#     return 


if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")

    
