from flask import (
    flash,
    render_template,
    redirect,
    request,
    session,
    url_for,
    Response
)
from twilio.twiml.voice_response import VoiceResponse, Dial
from flask import Flask
import flask
import urllib2
from datetime import datetime
import requests
import json
from twilio.rest import Client
import time


app = Flask(__name__)

bytesPersecond = 64000

def twiml(resp):
    resp = flask.Response(str(resp))
    resp.headers['Content-Type'] = 'text/xml'
    return resp

@app.route('/')
@app.route('/ivr')
def home():
    return render_template('index.html')

token = 'yourQuickBaseToken'

@app.route("/ivr/playaudio/<digits>", methods=['GET'])
def playaudio(digits):
    #response = VoiceResponse()
    #response.say("Please wait",voice="alice", language="en-GB", loop=1)
    #pudId = request.form['Digits']
    print "playaudio digits "+str(digits)
    
    r = requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'GetLessonForId', 'Id': str(digits)})
    lesson = r.json()
    print "playaudio lesson "+str(lesson)
    print "playaudio LessionUrl "+str(lesson['LessionUrl'])        
    def generateAudio():
            req = urllib2.Request(lesson['LessionUrl'])
            req.add_header('Authorization', token)
            #req.add_header('Range', "bytes=0-")
            fwav = urllib2.urlopen(req)
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
                #nLoops = nLoops+1
    return Response(generateAudio(), mimetype="audio/mpeg")

@app.route('/ivr/playlesson', methods=['POST'])
def playlesson():
    selected_option = int(request.form['Digits'])
    r = requests.get('https://hackathon20-nsiwale.quickbase.com/up/bqyv7jbgt/a/r10/e11/v0', allow_redirects=True)
    print r.content

    print "playlesson selected_option "+str(selected_option)
    response = VoiceResponse()
    #r = requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'GetLessonForId', 'Id': str(selected_option)})
    #lesson = r.json()
    #print "playlesson lesson "+str(lesson)
    response.play(url=url_for('playaudio',digits=str(selected_option)), loop=1)
    #r = requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'GetLessonForId', 'Id': str(selected_option)})
    #lesson = r.json()
    #print "playlesson lesson "+str(lesson)
    #response.play(url='lesson['LessionUrl']', loop=1)
    return twiml(response)

def _gotopub(response):
    with response.gather(
        numDigits=6, action=url_for('playlesson'), method="POST"
    ) as g:
        g.say("Please enter the publication 6 digit ID.",
              voice="alice", language="en-GB", loop=1)

    return response

@app.route('/ivr/subtoclass/<options>', methods=['POST'])
def subtoclass(options):
    optionsrec = json.loads(options)
    selected_option = int(request.form['Digits'])
    response = VoiceResponse()
    requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'AddStudentToSub'
    , 'PhoneNumber': request.form['Caller'], 'UniqueClassId': optionsrec[selected_option]['UniqueClassId']})
    response.say("Thank you for subscribing to the "+optionsrec[selected_option]['Name']+" class. "+" Goodbye")


    return twiml(response)

@app.route("/ivr/searchclass", methods=['POST'])
def searchclass():
    time.sleep(2)
    recording_url = request.form['RecordingUrl']
    response = VoiceResponse()
    print "startstream "+str(request)
    dict = request.form
    for key in dict:
        print 'searchclass form key '+dict[key]+" key "+key

    #response.say("Please wait")
    r = requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'SeachClass', 'Url': recording_url})
    options = r.json()

    print "startstream options "+str(options)
    try:
        message = "Please select the class to subsribe to."
        n = 0
        print options[0]['Name']
        for option in options:
            message = message+" Press "+str(n)+" to subsribe to the "+option['Name']+" class."
            n = n+1
    
        with response.gather(
            num_digits=1, action=url_for('subtoclass',options=json.dumps(options)), timeout=10, method="POST"
        ) as g:
            g.say(message=message, loop=1)
    except:
        with response.gather(timeout="1"
        ) as g:
            g.say("Sorry, I did not get that. Please state what kind of class you are looking for after the tone.",
                  voice="alice", language="en-GB", loop=1)
    
        response.redirect(url=url_for('searchclassrecording'), method="POST")
    return twiml(response)

@app.route("/ivr/searchclassrecording", methods=['POST'])
def searchclassrecording():
    response = VoiceResponse()
    r = response.record(max_length="8", action=url_for('searchclass'), method="POST",play_beep=True)
    print "_gotosub "+str(r)
    return twiml(response)

def _gotosub(response):
    with response.gather(timeout="1"
    ) as g:
        g.say("Please state what kind of class you are looking for after the tone.",
              voice="alice", language="en-GB", loop=1)
    
    response.redirect(url=url_for('searchclassrecording'), method="POST")

    #response.say("Please state what kind of class you are looking for after the tone.")
    #r = response.record(max_length="2", action=url_for('searchclass'), method="POST",transcribe=True)
    

    return response

@app.route("/ivr/playaudiourl/<url>", methods=['GET'])
def playaudiourl(url):
    print "playaudiourl url "+str(url)
    #response = VoiceResponse()
    #response.say("Please wait",voice="alice", language="en-GB", loop=1)
    #pudId = request.form['Digits']
    def generateAudioUrl():
            req = urllib2.Request(url)
            req.add_header('Authorization', token)
            #req.add_header('Range', "bytes=0-")
            fwav = urllib2.urlopen(req)
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
                #nLoops = nLoops+1
    return Response(generateAudioUrl(), mimetype="audio/mpeg")

@app.route('/ivr/subtolesson/<options>', methods=['POST'])
def subtolesson(options):
    parsedoptions = json.loads(options)
    selected_option = int(request.form['Digits'])
    print "subtolesson "+str(selected_option)
    print "subtolesson  options "+str(optionsn)
    response = VoiceResponse()
    response.play(url=url_for('playaudiourl',url=parsedoptions[selected_option]['LessionUrl']), loop=1)
    return twiml(response)


@app.route("/ivr/searchlesson", methods=['POST'])
def searchlesson():
    #time.sleep(5)
    recording_url = request.form['RecordingUrl']
    response = VoiceResponse()
    print "searchlesson "+str(request)
    print "searchlesson recording_url "+str(recording_url)
    dict = request.form
    for key in dict:
        print 'searchlesson form key '+dict[key]+" key "+key

    r = requests.post("https://v4z3nmrz83.execute-api.us-east-1.amazonaws.com/PunzilaStage/lesson", json={'Action': 'SeachLesson', 'Url': recording_url})
    options = r.json()
    print "searchlesson "+str(options)
    message = "Please select the lesson to play."
    try:
        n = 0
        print options[0]['Title']
        for option in options:
            message = message+" Press "+str(n)+" to play to "+option['Title']+"."
            n = n+1
    
        with response.gather(
            num_digits=1, action=url_for('subtolesson',options=json.dumps(options)),timeout=10,  method="POST"
        ) as g:
            g.say(message=message, loop=1)
    except:
        with response.gather(timeout="1"
        ) as g:
            g.say("Sorry, I did not get that. Please state the type of lession you are looking for after the tone.", loop=1)
    
        response.redirect(url=url_for('searchlessonrecording'), method="POST")
    return twiml(response)

@app.route("/ivr/searchlessonrecording", methods=['POST'])
def searchlessonrecording():
    response = VoiceResponse()
    r = response.record(max_length="8", action=url_for('searchlesson'),trim=False, method="POST",play_beep=True)
    print "_gotosub "+str(r)
    return twiml(response)

def _gotosearch(response):
    with response.gather(timeout="1"
    ) as g:
        g.say("Please state the type of lession you are looking for after the tone", loop=1)
    response.redirect(url=url_for('searchlessonrecording'), method="POST")

    return response

@app.route('/ivr/welcome', methods=['POST'])
def welcome():
    response = VoiceResponse()
    print "welcome "+str(request)
    dict = request.form
    for key in dict:
        print 'welcome form key '+dict[key]+" key "+key
    user = request.form['From']
    with response.gather(
        num_digits=1, action=url_for('menu'), method="POST"
    ) as g:
        g.say(message="Welcome to Punzila. "+
              "Please press 1 to go to lession. " +
              "Press 2 to subsribe to class. "+
              "Press 3 to search for lession. "+
              "Press 4 to go to bookmarks. ", loop=1)
    return twiml(response)


@app.route('/ivr/menu', methods=['POST'])
def menu():
    selected_option = request.form['Digits']
    option_actions = {'1': _gotopub,
                      '2': _gotosub,
                      '3': _gotosearch}

    if option_actions.has_key(selected_option):
        response = VoiceResponse()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()



def _redirect_welcome():
    response = VoiceResponse()
    response.say("Returning to the main menu")
    response.redirect(url_for('welcome'))

    return twiml(response)
