import re
import sys
import requests
from itertools import chain

RUNLOG_URL = 'https://run-log.com/'

def open_run_log_session(user,sessionid):
    run_log_session = requests.session()
    run_log_session.cookies.set("sessionid", sessionid, domain="run-log.com")
    return run_log_session


def get_num_of_pages(session):
    def extract_pagenum(page_str):
        return int(page_str.replace('page=', ''))
    training_list = session.get(RUNLOG_URL + 'training/list')
    pages = re.findall('page=\d+', training_list.text)
    num_of_page = max([extract_pagenum(page_str) for page_str in pages])
    print('Found {} pages of training to download.'.format(num_of_page))
    return num_of_page


def workout_ids(session, num_of_pages):
    url_template = RUNLOG_URL + 'training/list?page={}'
    def extract_id(s):
        return int(s.replace('show_workout(', ''))
    def ids_from_page(page_num):
        page_code = session.get(url_template.format(page_num))
        workouts = re.findall('show_workout\(\d+', page_code.text)
        return [extract_id(workout_str) for workout_str in workouts]
    def get_ids(pages):
        print("Fetching workouts from {} pages.".format(pages))
        return [ids_from_page(page_num) for page_num in range(1, pages + 1)]
    return list(chain(*get_ids(num_of_pages)))


def get_id(page):
    id = re.findall('wt_id&quot;: \d+', page.text)[0]
    return id.replace('wt_id&quot;: ', '')


def get_date(page):
    date = re.findall('Data:</span><span class="value">\d+-\d+-\d+', page.text)[0]
    return date.replace('Data:</span><span class="value">', '')

def get_workout_type(page):
    workout_type = re.findall('<h2>Aktywność: \w+', page.text)[0]
    return workout_type.replace('<h2>Aktywność: ', '')
            

def gpx_ids(session, workouts):
    url_template = RUNLOG_URL + 'workout/workout_show/{}'
    print("Fetching workouts in search for gpx ids.")
    ids = []
    for count, workout_id in enumerate(workouts):
        page_code = session.get(url_template.format(workout_id))
        print('{}/{}'.format(count + 1, len(workouts)))
        try:
            workout = get_id(page_code), get_date(page_code), get_workout_type(page_code)
            ids.append(workout)
        except:
            print('No gpx found for workout id {}!'.format(workout_id))
            pass
    print(ids)
    return ids


def save_gpx(gpx, id, day, workout_type):
    with open("{}_{}_{}.gpx".format(day, id, workout_type), "w") as f:
        f.write(gpx)


def download_gpxies(session, ids):
    url_template = RUNLOG_URL + 'tracks/export_workout_track/'+username+'/{}/gpx'
    def get_gpx(id):
        return session.get(url_template.format(id)).text
    def correct_dates(gpx):
        return re.sub('\d+-\d+-\d+', day, gpx)
    def fill_activity_type(gpx):
        STRAVA_WORKOUT_TYPE = "WORKOUT"
        if workout_type == "Spacer":
            STRAVA_WORKOUT_TYPE = "WALK"
        if workout_type == "Rower":
            STRAVA_WORKOUT_TYPE = "RIDE"
        if workout_type == "Bieganie" or workout_type == "Running" or workout_type == "Trening" or workout_type == "Bieg":
            STRAVA_WORKOUT_TYPE = "RUN"
        if workout_type == "Basen":
            STRAVA_WORKOUT_TYPE = "SWIM"
        if workout_type == "Siłownia":
            STRAVA_WORKOUT_TYPE = "WORKOUT"
        if workout_type == "Rower stacjonarny":
            STRAVA_WORKOUT_TYPE = "VIRTUALRIDE"
        return re.sub('<trk><trkseg>', '<trk><type>'+STRAVA_WORKOUT_TYPE+'</type><trkseg>', gpx)
    for count, (id, day, workout_type) in enumerate(ids):
        print("Downloading gpx: {} {}/{}".format(id, count + 1, len(ids)))
        gpx = fill_activity_type(correct_dates(get_gpx(id)))
        save_gpx(gpx, id, day, workout_type)


username = sys.argv[1]
sessionid = sys.argv[2]

run_log_session = open_run_log_session(username,sessionid)
ids = gpx_ids(run_log_session, workout_ids(run_log_session, get_num_of_pages(run_log_session)))
#ids = gpx_ids(run_log_session, workout_ids(run_log_session, 1))
download_gpxies(run_log_session, ids)

