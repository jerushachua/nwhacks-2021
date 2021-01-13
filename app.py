# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap
from datetime import datetime
from google.cloud import storage
from google.cloud import vision
from google.cloud import language_v1

import requests
import base64
import json
import pytz
import os
import re

try:
    import urlparse
    from urllib import urlencode
except: # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode


app = Flask(__name__) 

Bootstrap(app)

os.environ['NO_PROXY'] = '127.0.0.1'

GCLOUD_PDF_BUCKET_NAME = 'course-outlines-nwhacks'
GCLOUD_TEXT_BUCKET_NAME = 'course-texts-nwhacks'

# prod
# BASE_URL = 'www.coursecalendar.online'
BASE_URL = 'http://localhost:5000/'

def send_pdf_gcloud(filename):

    # development 
    # use service account credentials by specifying the private key
    # storage_client = storage.Client.from_service_account_json('secrets/nwhacks-2021-a6f652bb1912.json')

    # prod 
    data = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    print(data)
    print(os.listdir('/'))

    with open(GOOGLE_APPLICATION_CREDENTIALS, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    storage_client = storage.Client.from_service_account_json(GOOGLE_CREDENTIALS)

    # upload pdf to bucket
    bucket = storage_client.get_bucket(GCLOUD_PDF_BUCKET_NAME)
    object_name_in_gcs_bucket = bucket.blob(filename)
    object_name_in_gcs_bucket.upload_from_filename(filename)

    gcs_source_uri = 'gs://' + GCLOUD_PDF_BUCKET_NAME + '/' + filename
    gcs_destination_uri = 'gs://' + GCLOUD_TEXT_BUCKET_NAME + '/' + filename
    return detect_text_from_pdf(gcs_source_uri, gcs_destination_uri)


def detect_text_from_pdf(gcs_source_uri, gcs_destination_uri):

    mime_type = 'application/pdf'
    batch_size = 50

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(
        gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size)

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)

    operation = client.async_batch_annotate_files(
        requests=[async_request])

    print('Waiting for the operation to finish.')
    operation.result(timeout=10000)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)
    blob_list = list(bucket.list_blobs(prefix=prefix))

    # Process the first output file from GCS.
    # Since we specified batch_size=2, the first response contains
    # the first two pages of the input file.
    output = blob_list[0]

    json_string = output.download_as_string()
    response = json.loads(json_string)
    
    full_text = ''
    for res in response['responses']:
        full_text = full_text + res['fullTextAnnotation']['text']

    return text_to_date({ 'data': full_text })


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
    res = json.loads(response.text)

    if response.status_code == 200: 
        return date_to_calendar(json.loads(response.text), data["data"])
    if response.status_code in [414, 500] :
        return render_template("index.html", text="That file is too large to parse properly. Try another file?", show_upload_button=True)
    elif not len(res):
        return render_template("index.html", text="We couldn't find any events in that file. Try another file?", show_upload_button=True)


def date_to_calendar(data, original_text):

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
                datetime(int(year), int(month), int(day))
            except ValueError:
                isValidDate = False
            if isValidDate: 
                
                date = datetime(year=int(year), month=int(month), day=int(day))
                startdate = year + month + day
                enddate = year + month + str(int(day) + 1)
                date_url = calendar_url + "?dates=" + startdate.strip('-') + '/' + enddate.strip('-') 
                dates.append([date, date_url])
        
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
        params = { 'filename': uploaded_file.filename }
        # requests.get(BASE_URL + '/upload', params=params)
        # return render_template("index.html", title="Got your file!", text="Parsing file ... ", show_upload_button=False, loading=True)
        return send_pdf_gcloud(uploaded_file.filename)
    else:
        return render_template("index.html", title="Welcome!", text="Upload a course outline to get started. ", show_upload_button=True)


@app.route('/upload', methods=['GET'])
def parse_file():
    uploaded_file = request.args['filename']
    return send_pdf_gcloud(uploaded_file)

# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

