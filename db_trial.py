"""
Just to test database functions,
outside of Flask.

We want to open our MongoDB database,
insert some memos, and read them back
"""
import arrow

# Mongo database
from pymongo import MongoClient
import CONFIG
try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

#
# Insertions:  I commented these out after the first
# run successfuly inserted them
# 

record = { "type": "dated_memo", 
           "date":  arrow.utcnow().naive,
           "text": "This is a sample memo"
          }
collection.insert(record)

record = { "type": "dated_memo", 
           "date":  arrow.utcnow().replace(days=+1).naive,
           "text": "Sample one day later"
          }
collection.insert(record)
collection.remove({})
#
# Read database --- May be useful to see what is in there,
# even after you have a working 'insert' operation in the flask app,
# but they aren't very readable.  If you have more than a couple records,
# you'll want a loop for printing them in a nicer format. 
#

records = [ ] 
for record in collection.find( { "type": "dated_memo" } ):
   records.append(
        { "type": record['type'],
          "date": arrow.get(record['date']).to('local').isoformat(),
           "text": record['text']
    })

print(records)
