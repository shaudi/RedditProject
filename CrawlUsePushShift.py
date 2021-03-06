from urllib2 import Request, urlopen, URLError
import json
import pandas as pd
import requests
import time
import datetime
import pymysql

mysql_conn = pymysql.connect(host="*",
                               user="*",
                               password="*",
                               db="*",
                               port=3306,
                               use_unicode=True,
                               charset="utf8")

cursor = mysql_conn.cursor()


data = {}

# get submission data and use its id to get all comment
submission = 'https://api.pushshift.io/reddit/search/submission/?subreddit=Bitcoin&after=1d&size=500'
r = requests.get(submission)
json_data = r.json()
SubDF = pd.DataFrame(json_data['data'])
# print SubDF['selftext']

filename = 'Bitcoin' + 'PS_file.json'
with open( filename, 'w') as f:

  for index in range( len(SubDF) )  :
    timeArray = time.localtime(SubDF['created_utc'][index])
    readabletime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    #put poster data in dic
    data['author'] = str(SubDF['author'][index])
    data['created_at'] = str(readabletime)
    data['title'] = SubDF['title'][index]
    data['type'] = "Post"
    data['ReplyToWho'] = ''
    data['text'] = SubDF['selftext'][index]

    # put in to data base
    sqldata = "INSERT INTO reddit_data (title, author, created_at, text, type, ReplyToWho )  VALUES (%s,%s,%s,%s,%s,%s)"
    cursor.execute(sqldata, (
        SubDF['title'][index], str(SubDF['author'][index]), str(readabletime), SubDF['selftext'][index], "Post", '' ))

    json.dump(data, f)
    f.write('\n')

    # get the one submission all comment by id
    comments = 'https://api.pushshift.io/reddit/submission/comment_ids/' + SubDF['id'][index]
    r = requests.get(comments)
    json_data = r.json()
    ComsDF = pd.DataFrame(json_data['data'])

    if not ComsDF.empty:
        for indexC in range(len(ComsDF[0])):
            comment = 'https://api.pushshift.io/reddit/search/comment/?ids=' + ComsDF[0][indexC]
            # print( comment )
            r = requests.get(comment)
            json_data = r.json()
            ComDF = pd.DataFrame(json_data['data'])
            commentdata = {}
            commentdata['author'] = str(ComDF['author'][0])

            # change UNIX-Time to readableTime
            timeArray = time.localtime(ComDF['created_utc'][0])
            readabletime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

            commentdata['created_at'] =  str(readabletime)
            commentdata['title'] = SubDF['title'][index]
            commentdata['type'] = "Reply"
            # get the parent_id
            parent_id = ComDF['parent_id'][0]
            # parent_id = parent_id[0]
            parent_id = parent_id[3:]
            # -----------------
            # get parent real name
            parent = 'https://api.pushshift.io/reddit/search/submission/?size=1&ids=' + parent_id
            # print( parent )
            r = requests.get(parent)
            json_data = r.json()
            ParDF = pd.DataFrame(json_data['data'])
            if not ParDF.empty:
                parent_name = ParDF['author'][0]
            # ------------------
            commentdata['ReplyToWho'] = str( parent_name )
            commentdata['text'] = ComDF['body'][0]

            # put in to data base
            sqldata = "INSERT INTO reddit_data (title, author, created_at, text, type, ReplyToWho )  VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sqldata, (
                SubDF['title'][index], str(ComDF['author'][0]), str(readabletime), ComDF['body'][0], "Reply", str( parent_name ) ))

            json.dump(commentdata, f)
            f.write('\n')

f.close()
mysql_conn.commit()
cursor.close()
mysql_conn.close()

