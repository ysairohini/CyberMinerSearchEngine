
from flask import Flask, render_template, request, json, redirect,url_for
from flaskext.mysql import MySQL
from flask import jsonify
import math
import csv
import config
import time
import atexit
import requests
from pytrends.request import TrendReq
import re

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = config.MYSQL_DATABASE_USER
app.config['MYSQL_DATABASE_PASSWORD'] = config.MYSQL_DATABASE_PASSWORD
app.config['MYSQL_DATABASE_DB'] = config.MYSQL_DATABASE_DB
app.config['MYSQL_DATABASE_HOST'] = config.MYSQL_DATABASE_HOST
app.config['MYSQL_DATABASE_PORT'] = config.MYSQL_DATABASE_PORT
mysql.init_app(app) 
pytrend = TrendReq()
# set up

def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')

def getP(i):
    return "%" + i.strip() + "%"
def getQuery(q):
    query = "SELECT * FROM tbl_test where "
    args = []
    orList = re.split(r'or|\|', q, flags=re.IGNORECASE)
    for i in range(len(orList)):
        query = query + "("
        andList = re.split(r'and|&', orList[i], flags=re.IGNORECASE)
        arT = ""
        arD = ""
        tlist = []
        dlist = []
        containNot = False
        for j in range(len(andList)):
            val = andList[j]
            if re.search(r'not', val):
                arT = arT + "title not like BINARY %s"
                arD = arD + "description not like BINARY %s"
                val = getP(re.sub(r"not","", val))
                tlist.append(val)
                dlist.append(val)
                containNot = True
            else:
                arT = arT + "title like BINARY %s"
                arD = arD + "description like BINARY %s"
                tlist.append(getP(val))
                dlist.append(getP(val))
            if j + 1 != len(andList):
                arT = arT + " and "
                arD = arD + " and "
        if containNot:
            query =  query + arT + " and " + arD
        else:
            query =  query + arT + " or " + arD
        query = query + ")"
        args = args + tlist + dlist
        if i + 1  != len(orList):
            query = query + " or "
    query = query + " ORDER BY title ASC"
    print(query)
    print(args)
    args = tuple(args)
    return query, args
        

try:
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_test")
    data = cursor.fetchall()
    if len(data) == 0 :
        print("setting up database")
        with open('./dataset/data.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count != 0:
                    cursor.execute("INSERT INTO tbl_test(title, description, url) VALUES (%s, %s, %s)", (deEmojify(row[0]), deEmojify(row[2]), row[1]))
                line_count += 1
            data = cursor.fetchall()
            conn.commit()
    else:
        print("database is ready to use")
except Exception as e:
    print(e)
    cursor.execute("CREATE TABLE tbl_test( id INT AUTO_INCREMENT PRIMARY KEY, title text , description text,url text);")
    print("please try again, table has been created")
    exit()
finally:
    cursor.close()
    conn.close()

def clean_out_of_date_url():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_test")
    data = cursor.fetchall()
    for result in data:
        request = requests.get(result[3])
        if request.status_code != 200:
            print("removing", result[3])
            cursor.execute("DELETE FROM tbl_test WHERE id = %s", ( result[0]))
            conn.commit()
    cursor.close()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_out_of_date_url, trigger="interval", seconds=config.OUT_OF_DATE_URL_CLEAN_INTERVAL)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

app.secret_key = 'secret key'

@app.route("/") # define an url "/" home page
def main():   
     return render_template('home.html')
    
@app.route("/search", methods=['POST'])
def search():
    try:

        conn = mysql.connect()
        cursor = conn.cursor()
        if(not "search" in request.form):
            return  redirect("/")
        _keyword = request.form['search']
        if(not(_keyword and _keyword.strip())):
            return  redirect("/")
        
        # Filtering out symbols that are not meaningful 
        _keyword = deEmojify(_keyword).strip()

        json_data=[]
        query, args = getQuery(_keyword)
        cursor.execute(query, args)
        data = cursor.fetchmany(config.MAX_RESULT_SIZE)
        if len(data)>= 0 :
            count = 0
            row_headers=[x[0] for x in cursor.description]
            for result in data:
                json_data.append(dict(zip(row_headers,result)))
                count +=1
            return json.dumps({"message":"get Successful", "data":json_data}) 
        else:
            return render_template ('error.html', error='no search result')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()

@app.route("/predict", methods=['POST'])
def predict():
    try:

        conn = mysql.connect()
        cursor = conn.cursor()
        if(not "search" in request.form):
            return  redirect("/")
        _keyword = request.form['search']
        if(not(_keyword and _keyword.strip())):
            return  redirect("/")
        # Filtering out symbols that are not meaningful 
        _keyword = deEmojify(_keyword).strip()
        cursor.execute("SELECT * FROM tbl_test where title like BINARY %s ",('%'+_keyword+'%'))
        data = cursor.fetchmany(5)
        json_data=[]
        suggestList = pytrend.suggestions(keyword=_keyword)
        for a in suggestList:
            json_data.append(a)
        if len(data)>= 0 :
            row_headers=[x[0] for x in cursor.description]
            
            count = 0
            for result in data:
                json_data.append(dict(zip(row_headers,result)))
                count +=1
            return json.dumps({"message":"get Successful", "data":json_data}) 
        else:
            return render_template ('error.html', error='no search result')

    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
