# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap

import requests
import base64
import json


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

  text_to_date(response.text)
  return render_template('loading.html')

def text_to_date(data):
    
    if not data:
       return render_template('index.html') 

    print(data)

    url = "https://webknox-text-processing.p.rapidapi.com/text/dates"
    querystring = {"text":"Jerusha Chua\ "}

    headers = {
    'x-rapidapi-key': "384dd2b48dmsh6a4567223470c4bp19ca4ejsndb0512e6a247",
    'x-rapidapi-host': "webknox-text-processing.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    print(response.text)


# A welcome message to test our server
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/', methods=['POST'])
def upload_file():

    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        send_pdf(uploaded_file.filename) 

        return redirect(url_for('success'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

