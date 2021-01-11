### Development set up

Create a python virtual environment

`python3 -m venv`

Start the environment
`source venv/bin/activate`

Install dependencies
`pip3 install -r requirements.txt` 

Run the app
`python app.py`

# Course Calendar

## Inspiration
We wanted to build an app that could parse course outlines and automatically add important dates to our calendar. 

## What it does
 * You can upload a course outline to www.coursecalendar.online
 * We extract important dates from your file - assignment due dates, exams, etc. 
 * Add these dates to your calendar with a single click! 
 * Save time by avoiding manually inputting all those dates

## How we built it
We used Flask for the API to easily handle the data flowing through our app in Python. Bootstrap and HTML for the frontend. Heroku for deployment and domain.com for our domain name. 

## Challenges
We were limited by the APIs we could choose from - since there were only a few free options. These APIs had other roadblocks like rate limits, poor documentation, and were sometimes unreliable. For example, load testing found that the PDF to text API fails with large file uploads and the NLP API sometimes had issues parsing a large amount of text for dates. 

