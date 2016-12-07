import re
import requests
from itertools import chain

def open_run_log_session(user, passwd):
    run_log_session = requests.session()
    run_log_session.post('https://run-log.com/account/login/', data={'username': user,
                                                                     'password': passwd})
    return run_log_session


def get_num_of_pages(session):
    def extract_pagenum(page_str):
        return int(page_str.replace('page=', ''))
    training_list = session.get('https://run-log.com/training/list')
    pages = re.findall('page=\d+', training_list.text)
    num_of_page = max([extract_pagenum(page_str) for page_str in pages])
    print('Found {} pages of training to download.'.format(num_of_page))
    return num_of_page


def workout_ids(session, num_of_pages):
    def extract_id(s):
        return int(s.replace('show_workout(', ''))
    def ids_from_page(page_num):
        print(page_num)
        page_code = session.get('https://run-log.com/training/list?page={}'.format(page_num))
        workouts = re.findall('show_workout\(\d+', page_code.text)
        return [extract_id(workout_str) for workout_str in workouts]
    def get_ids(pages):
        return [ids_from_page(page_num) for page_num in range(1, pages + 1)]
    return list(chain(*get_ids(num_of_pages)))


def gpx_ids(session, workouts):
    k = []
    for count, workout_id in enumerate(workouts):
        q = session.get('https://run-log.com/workout/workout_show/{}'.format(workout_id))
        print('{}/{}'.format(count, len(workouts)))
        try:
            z = re.findall('wt_id&quot;: \d+', q.text)[0]
            c = re.findall('Data:</span><span class="value">\d+-\d+-\d+', q.text)[0]
            k.append((z.replace('wt_id&quot;: ', ''), c.replace('Data:</span><span class="value">', '')))
        except:
            print('No gpx!')
            pass
    return k


def download_gpxies(ids):
    for count, (id, day) in enumerate(ids):
        r = run_log_session.get('https://run-log.com/tracks/export_workout_track/Rysmen/{}/gpx'.format(id))
        a = re.sub('\d+-\d+-\d+', day, r.text)
        a = re.sub('<trk><trkseg>', '<trk><type>RUNNING</type><trkseg>', a)
        with open("dupa/{}_{}.gpx".format(day, id), "w") as f:
            print('{}/{}'.format(count, len(k)))
            f.write(a)


run_log_session = open_run_log_session('Rysmen', 'testowe')
k = gpx_ids(run_log_session, workout_ids(run_log_session, get_num_of_pages(run_log_session)))
download_gpxies(k)
