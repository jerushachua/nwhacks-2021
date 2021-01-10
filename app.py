# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap

import requests
import base64
import json
import pytz
import os
import datetime

try:
    import urlparse
    from urllib import urlencode
except: # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode


app = Flask(__name__) 

Bootstrap(app)

os.environ['NO_PROXY'] = '127.0.0.1'



def send_pdf(filename): 

    data = {} 
    with open(filename, 'rb') as pdf: 
        s = base64.b64encode(pdf.read())
        data["data"] = s.decode("utf-8")

    url = "https://pdf-to-text.p.rapidapi.com/text-extraction"
    headers = {
        'content-type': "application/json",
        'x-rapidapi-key': "384dd2b48dmsh6a4567223470c4bp19ca4ejsndb0512e6a247",
        'x-rapidapi-host': "pdf-to-text.p.rapidapi.com"
    }
    
    response = requests.request("POST", url, data=json.dumps(data), headers=headers)

    if response.status_code == 201: 
        return text_to_date(json.loads(response.text))
    else:
        return render_template("index.html", text="We couldn't parse that file. Try another file?", show_upload_button=True)


def text_to_date(data):
    
    if not len(data):
       return render_template('failed_to_parse.html') 

    querystring = {
      'text': data["data"],
      'Content-Type': 'application/json'
    } 

    url = "https://webknox-text-processing.p.rapidapi.com/text/dates"

    headers = {
    'x-rapidapi-key': "384dd2b48dmsh6a4567223470c4bp19ca4ejsndb0512e6a247",
    'x-rapidapi-host': "webknox-text-processing.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code == 200: 
        return date_to_calendar(json.loads(response.text), data["data"])
    if response.status_code == 414:
        return render_template("index.html", text="That file is too large to parse properly. Try another file?", show_upload_button=True)
    else:
        return render_template("index.html", text="We couldn't find any events in that file. Try another file?", show_upload_button=True)


def date_to_calendar(data, original_text):

    # https://stackoverflow.com/questions/5831877/how-do-i-create-a-link-to-add-an-entry-to-a-calendar/19867654#19867654
    calendar_url = "https://calendar.google.com/calendar/r/eventedit"

    if not len(data):
        return render_template("index.html", text="We couldn't find any events in that file. Try another file?", show_upload_button=True)
    
    dates = []
    for item in data:

        date_vals = item['normalizedDate'].split('-')
        if len(date_vals) == 3: 
            year, month, day = date_vals
            isValidDate = True
            try:
                datetime.datetime(int(year), int(month), int(day))
            except ValueError:
                isValidDate = False
            if isValidDate: 
                date = datetime.datetime(year=int(year), month=int(month), day=int(day))
                dates.append(date)
    
    print(dates)
    return render_template('file_success.html', dates=dates)
    

# Index
@app.route('/')
def index():
    return render_template("index.html", title="Welcome!", text="Upload a course outline to get started. ", show_upload_button=True)


@app.route('/', methods=['POST'])
def upload_file():

    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        return send_pdf(uploaded_file.filename) 


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

