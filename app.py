# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap

import requests
import base64
import json


import google.oauth2.credentials
import google_auth_oauthlib.flow
from oauth2client import client
from googleapiclient import sample_tools


# Use the client_secret.json file to identify the application requesting
# authorization. The client ID (from that file) and access scopes are required.
flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'])

flow.redirect_uri = 'https://www.example.com/oauth2callback'

authorization_url, state = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true')


app = Flask(__name__) 


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

  text_to_date(json.loads(response.text))


def text_to_date(data):
    
    if not data:
       return render_template('index.html') 

    querystring = {
      'text': data["data"],
      'Content-Type': 'application/json'
    } 
    print(querystring)

    url = "https://webknox-text-processing.p.rapidapi.com/text/dates"

    headers = {
    'x-rapidapi-key': "384dd2b48dmsh6a4567223470c4bp19ca4ejsndb0512e6a247",
    'x-rapidapi-host': "webknox-text-processing.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    date_to_calendar(json.loads(response.text))
    return render_template('calendar.html')


def date_to_calendar(data):

    if not data:
        return render_template('index.html') 
    
    print(data)
    


# Index
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def upload_file():

    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        send_pdf(uploaded_file.filename) 

        return render_template('file_success.html')


# Post file upload
@app.route('/success')
def success():
    return render_template('file_success.html')


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

