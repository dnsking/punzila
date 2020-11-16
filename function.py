import json
import random
import boto3
import secrets
import string
import datetime
import pymysql
import time
import base64
from botocore.vendored import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen


#rds settings
rds_host  = "dhost"
name = "admin"
password = "dbpassowrd"
db_name = "punziladb"

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("ERROR: Unexpected error: Could not connect to MySQL instance.")
    print(e)

def addStudentToSub(phoneNumber,UniqueClassId):
    with conn.cursor() as cur:
        values = ' values('+phoneNumber+','+ UniqueClassId+')'
        cur.execute('insert into StudentsClassSubsTable (phoneNumber, UniqueClassId) Values(%s,%s)',(phoneNumber,UniqueClassId))
        conn.commit()

def getsStudentForSub(UniqueClassId):
    with conn.cursor() as cur:
        values = ' values('+phoneNumber+','+ UniqueClassId+')'
        cur.execute('insert into StudentsClassSubsTable (phoneNumber, UniqueClassId)'+values)
        conn.commit()

def createStudents():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS StudentsTable(phoneNumber varchar(255) NOT NULL, name varchar(255) NOT NULL, PRIMARY KEY (phoneNumber))")
        conn.commit()

def createStudentsClassSubsTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS StudentsClassSubsTable(id INT AUTO_INCREMENT PRIMARY KEY, phoneNumber varchar(255) NOT NULL, UniqueClassId varchar(255) NOT NULL)")
        conn.commit()

def createStudentsClassLessonBookmarksTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS StudentsClassLessonBookmarksTable(id INT AUTO_INCREMENT PRIMARY KEY, phoneNumber varchar(255) NOT NULL, UniqueLessonId varchar(255) NOT NULL)")
        conn.commit()

def createStudentsSavedRecordingTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS StudentsSavedRecordingTable(id INT AUTO_INCREMENT PRIMARY KEY, phoneNumber varchar(255) NOT NULL, link varchar(255) NOT NULL)")
        conn.commit()

def createTagsTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS TagsTable(id INT AUTO_INCREMENT PRIMARY KEY, Name varchar(255) NOT NULL, UniqueClassId varchar(255) NOT NULL)")
        conn.commit()

def createTopicsTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS TopicsTable(id INT AUTO_INCREMENT PRIMARY KEY, Name varchar(255) NOT NULL, UniqueLessonId varchar(255) NOT NULL)")
        conn.commit()

def createClassTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS ClassTable(id INT AUTO_INCREMENT PRIMARY KEY, Name varchar(255) NOT NULL, UniqueClassId varchar(255) NOT NULL)")
        conn.commit()


def createLessonTable():
    with conn.cursor() as cur:
        cur.execute("create table IF NOT EXISTS LessonTable(id INT AUTO_INCREMENT PRIMARY KEY, UniqueLessonId varchar(255) NOT NULL, Title varchar(255) NOT NULL, DatePublished varchar(255) NOT NULL, UniqueClassId varchar(255) NOT NULL, LessonURL varchar(255) NOT NULL)")
        conn.commit()
        
def insertProperty(data):
    with conn.cursor() as cur:
        values = ' values('+data['propertyId']+','+ data['locationName']+','+ data['locationactualName']+','+ data['sellerId']+','+ data['propertyType']+','+ data['price']+','+ data['size']+','+ data['note']+','+ data['bedroomCount']+','+ data['bathroomCount']+','+ json.dumps(data['amenities'])+','+ json.dumps(data['location'])+','+json.dumps(data['images']) +','+ data['currencyName']+','+ data['city']+','+ data['country']+')'
        cur.execute('insert into PropertySeenDBTable (propertyId, locationName, locationactualName, sellerId, propertyType, price, size, note, bedroomCount, bathroomCount, amenities, location, images, currencyName, city, country)'+values)
        conn.commit()
        
def getAllproperties():
    data = []
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM PropertySeenDBTable")
        rows = cur.fetchall()
        for row in rows:
            item = {"propertyId":row["propertyId"], "locationName":row["locationName"], "locationactualName":row["locationactualName"], "sellerId":row["sellerId"], "propertyType":row["propertyType"], "price":row["price"], "size":row["size"], "note":row["note"], "bedroomCount":row["bedroomCount"], "bathroomCount":row["bathroomCount"], "amenities":row["amenities"], "location":row["location"], "images":row["images"], "currencyName":row["currencyName"], "city":row["city"], "country":row["country"]}
            data.append(json.dumps(item))
    return data
    
def addNewLesson(Title,DatePublished,LessionUrl,UniqueLessonId,UniqueClassId,TopicsHolder):
    with conn.cursor() as cur:
        values = ' values('+Title+','+ DatePublished+','+ LessionUrl+','+ UniqueLessonId+','+ UniqueClassId+')'
        cur.execute('insert into LessonTable (Title, DatePublished, LessonURL, UniqueLessonId, UniqueClassId) Values(%s, %s, %s, %s, %s)'
        ,(Title,DatePublished,LessionUrl,UniqueLessonId,UniqueClassId))
        conn.commit()
    if TopicsHolder is not None:
        Tags = TopicsHolder.split(',')
        for tag in Tags:
            with conn.cursor() as cur:
                values = ' values('+tag+','+ UniqueLessonId+')'
                cur.execute('insert into TopicsTable (Name, UniqueLessonId) Values(%s, %s)',(tag.strip(),UniqueLessonId))
                conn.commit()
    
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM LessonTable ORDER BY id DESC LIMIT 1")
        newId = cur.fetchall()[0]['id']
        
        cur.execute("SELECT * FROM StudentsClassSubsTable WHERE UniqueClassId=%s", UniqueClassId )
        rows = cur.fetchall()
        for row in rows:
            sendSMS(row['phoneNumber'],"A new lesson titled "+Title+" has been posted. Use the code "+str(newId).zfill(6)+" to listen")
    

def addNewClass(Name,UniqueClassId,TagHolder):
    with conn.cursor() as cur:
        values = ' values('+Name+','+ UniqueClassId+')'
        cur.execute('insert into ClassTable (Name, UniqueClassId) Values(%s, %s)',(Name,UniqueClassId))
        conn.commit()
    if TagHolder is not None:
        Tags = TagHolder.split(',')
        for tag in Tags:
            with conn.cursor() as cur:
                values = ' values('+tag+','+ UniqueClassId+')'
                cur.execute('insert into TagsTable (Name, UniqueClassId) Values(%s, %s)',(tag.strip(),UniqueClassId))
                conn.commit()

def get_as_base64(url):
    return base64.b64encode(requests.get(url).content).decode('utf-8')
    
def audioToTranscript(link):
    base64data = get_as_base64(link)
    print(link)
    url = 'https://speech.googleapis.com/v1/speech:recognize?key=AIzaSyAVArvLpiAaq1Muod7UkL2Cj9zmcoZHPic'
    post_fields = {"config": {
    "encoding": "LINEAR16",
    "languageCode": "en-US",
    "enableWordTimeOffsets": False,
     "use_enhanced": True,
     "model": "phone_call" },"audio":{"content":base64data}}
    #request = Request(url, urlencode(post_fields).encode())
    #json = urlopen(request).read().decode()
    r = requests.post(url, json=post_fields)
    jsonresult = r.json()
    return jsonresult['results'][0]['alternatives'][0]['transcript']
        
def searchForClass(link):
    toSearchFor = audioToTranscript(link)
    
    print(toSearchFor)
    data = []
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM TagsTable WHERE LOWER(Name) LIKE %s",( toSearchFor.lower().strip(),))
        rows = cur.fetchall()
        for row in rows:
            print(row["UniqueClassId"])
            cur.execute("SELECT * FROM ClassTable WHERE UniqueClassId=%s",row["UniqueClassId"])
            classItem = cur.fetchall()[0]
            item = {"Name":classItem["Name"], "UniqueClassId":classItem["UniqueClassId"]}
            data.append(item)
    return data
    
def searchForLesson(link):
    toSearchFor = audioToTranscript(link)
    data = []
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM TopicsTable WHERE LOWER(Name) LIKE %s",(toSearchFor,))
        rows = cur.fetchall()
        for row in rows:
            cur.execute("SELECT * FROM LessonTable WHERE UniqueLessonId=%s",row["UniqueLessonId"])
            classItem = cur.fetchall()[0]
            #item = {"Title":classItem["Title"], "DatePublished":classItem["DatePublished"], "LessionUrl":classItem["LessonURL"], "UniqueLessonId":classItem["UniqueLessonId"], "UniqueClassId":classItem["UniqueClassId"]}
            item = {"Title":classItem["Title"],  "LessionUrl":classItem["LessonURL"]}
            data.append(item)
    return data
    
def getLessonForId(idk):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM LessonTable WHERE id=%s",(idk,))
        item = cur.fetchall()[0]
        return {"Title":item["Title"], "DatePublished":item["DatePublished"], "LessionUrl":item["LessonURL"], "UniqueLessonId":item["UniqueLessonId"], "UniqueClassId":item["UniqueClassId"]}
            
    
def lambda_handler(event, context):
    # TODO implement
    print(event)
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
  

    if event['Action'] == "ClassMod":
        return addNewClass(event['Name'],event['UniqueClassId'],event['Tags'])
    elif event['Action'] == "SeachClass":
        return searchForClass(event['Url'])
    elif event['Action'] == "AddStudentToSub":
        return addStudentToSub(event['PhoneNumber'],event['UniqueClassId'])
    elif event['Action'] == "SeachLesson":
        return searchForLesson(event['Url'])
    elif event['Action'] == "LessonMod":
        return addNewLesson(event['Title'],event['Date'],event['LessonData'],event['UniqueLessonId'],event['UniqueClassId'],event['Topic'])
    elif event['Action'] == "GetLessonForId":
        return getLessonForId(event['Id'])
    return {
        
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def sendSMS(phoneNumber,msg):
    sns = boto3.client('sns')
    number = phoneNumber
    sns.publish(PhoneNumber = number, Message=msg, MessageAttributes={'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': "Punzila"}, 'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Promotional'}})
    return "sent"
