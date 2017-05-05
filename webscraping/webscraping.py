import json
import os
import time
import urllib.parse
import urllib.request
import pyquery

WEB_SCRAPING    = False
CONTEST_PATH    = 'topcoderTCO17MMR1GraphDrawing'

DATA_PATH       = os.path.join(CONTEST_PATH, 'data')
with open('settings.json') as f:
    settings    = json.load(f)
    COOKIE      = settings['cookie']
with open(os.path.join(CONTEST_PATH, 'settings.json')) as f:
    settings        = json.load(f)
    RD              = str(settings['rd'])
    STANDINGS_URL   = 'https://community.topcoder.com/longcontest/stats/?&sr=1&nr=50000&module=ViewOverview&rd=' + RD
    USER_URL        = 'https://community.topcoder.com/longcontest/stats/?module=IndividualResultsFeed&rd={}&cr={}'
    TEST_CASE_URL   = 'https://community.topcoder.com/longcontest/stats/?module=ViewSystemTest&tid={}&rd={}&pm={}'

for name in 'users', 'test_cases':
    try:
        os.makedirs(os.path.join(DATA_PATH, name))
    except:
        pass

if WEB_SCRAPING:
    try:
        with urllib.request.urlopen(STANDINGS_URL) as url:
            with open(os.path.join(DATA_PATH, 'standings.html'), 'wb') as f:
                f.write(url.read())
    except:
        print('Failed web scraping ' + STANDINGS_URL)
        exit()

users = []
try:
    path = os.path.join(DATA_PATH, 'standings.html')
    with open(path) as f:
        standings = pyquery.PyQuery(f.read())
except:
    print('Not found ' + path)
    exit()
PM = urllib.parse.parse_qs(urllib.parse.urlparse(
    standings.find('.bodySubtitle a').attr('href')).query)['pm'][0]
for e in standings.find('.stat tr:nth-child(n+3)'):
    e = pyquery.PyQuery(e).find('td:nth-child(2)')
    user_name = e.text()
    user_id = urllib.parse.parse_qs(urllib.parse.urlparse(
        e.find('a').attr('href')).query)['cr'][0]
    users.append((user_name, user_id))

if WEB_SCRAPING:
    for user_name, user_id in users:
        try:
            with urllib.request.urlopen(USER_URL.format(RD, user_id)) as url:
                with open(os.path.join(DATA_PATH, 'users', user_name + '.xml'), 'wb') as f:
                    f.write(url.read())
        except:
            print('Failed web scraping ' + USER_URL.format(RD, user_id))
            exit()
        time.sleep(2)

try:
    path = os.path.join(DATA_PATH, 'users', users[0][0] + '.xml')
    with open(path, 'rb') as f:
        test_case_ids = [e.text for e in pyquery.PyQuery(f.read()).find('test_case_id')]
except:
    print('Not found ' + path)
    exit()

if WEB_SCRAPING:
    for test_case_id in test_case_ids:
        try:
            request = urllib.request.Request(TEST_CASE_URL.format(test_case_id, RD, PM), headers={ 'cookie': COOKIE })
            with urllib.request.urlopen(request) as url:
                with open(os.path.join(DATA_PATH, 'test_cases', test_case_id + '.html'), 'wb') as f:
                    f.write(url.read())
        except:
            print('Failed web scraping and skip ' + TEST_CASE_URL.format(test_case_id, RD, PM))
        time.sleep(2)

test_cases = []
failed_ids = []
for test_case_id in test_case_ids:
    try:
        with open(os.path.join(DATA_PATH, 'test_cases', test_case_id + '.html')) as f:
            s = pyquery.PyQuery(f.read()).find('pre').text()

        # lines = s.split('\n')
        # test_cases.append([
        #     lines[3:-2],
        #     int(lines[-2].split('=')[1]),
        #     int(lines[-1].split('=')[1]),
        # ])

        lines = s.split('\n')
        test_cases.append([
            int(lines[-2].split('=')[1]),
            { 'length': int(lines[-1].split('=')[1]) * 3 },
        ])

    except:
        failed_ids.append(test_case_id)

if WEB_SCRAPING:
    print('Web scraping finished. {} test cases skipped.'.format(len(failed_ids)))

for i, (user_name, user_id) in enumerate(users):
    try:
        path = os.path.join(DATA_PATH, 'users', user_name + '.xml')
        with open(path, 'rb') as f:
            es = pyquery.PyQuery(f.read()).find('testcase')
    except:
        print('Not found ' + path)
        exit()
    scores = []
    for e in es:
        e = pyquery.PyQuery(e)
        if e.find('test_case_id').text() not in failed_ids:
            scores.append(float(e.find('score').text()))
    users[i] = {
        'name': user_name,
        'scores': scores,
    }
path = os.path.join(DATA_PATH, CONTEST_PATH + '.json')
with open(os.path.join(DATA_PATH, CONTEST_PATH + '.json'), 'w') as f:
    json.dump({
        'test_cases': test_cases,
        'users': users,
    }, f, separators=(',', ':'))

print('Created ' + path)
