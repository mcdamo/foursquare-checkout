#!/usr/bin/env python3

import sys
from database import Database
import foursquare
import argparse
import json

# duplicated from database
import configparser

db = Database()

config = configparser.ConfigParser()
config.read('config.ini')
# Construct the client object
client = foursquare.Foursquare(client_id=config['FOURSQUARE']['CLIENT_ID'],
    client_secret=config['FOURSQUARE']['CLIENT_SECRET'],
    redirect_uri=config['FOURSQUARE']['CLIENT_CALLBACK'])

def auth():
    # Build the authorization url for your app
    auth_uri = client.oauth.auth_url()
    print(auth_uri);

def auth_redirect(code):
    # Interrogate foursquare's servers to get the user's access_token
    access_token = client.oauth.get_token(code)

    # Apply the returned access token to the client
    client.set_access_token(access_token)

    # Get the user's data
    user = client.users()
    #print(user)
    sql = "REPLACE INTO users (id, name, auth_token) VALUES (%(id)s, %(name)s, %(auth_token)s);"
    # join strings with spaces if not null
    name = ' '.join(filter(None, [ user['user'].get('firstName', None), user['user'].get('lastName', None) ]))
    fid = user['user']['id']
    print(fid + ': ' + name)
    cur = db.execute(sql, {'id': fid, 'name': name, 'auth_token': access_token})
    db.commit()

def insert_checkin(cx, user_id):
    cf = [
        'id',
        'user_id',
        'type',
        'timeZoneOffset',
        'createdAt',
        'private',
        'shout',
        'venue_id',
        'venue_name',
        'location',
        'event',
        'photos',
        'like',
        'post',
    ]
    sqlCheckin = "INSERT INTO checkins (" + \
        ','.join('`' + i + '`' for i in cf) + \
        ") VALUES (" + \
        ','.join('%(' + i + ')s' for i in cf) + \
        ");"
    cv = [
        'id',
        'name',
        'location_address',
        'location_crossStreet',
        'location_lat',
        'location_lng',
        'location_postalCode',
        'location_cc',
        'location_city',
        'location_state',
        'location_country',
        'location_formattedAddress',
        'categories',
        'closed',
    ]
    sqlVenue = "REPLACE INTO venues (" + \
        ','.join('`' + i + '`' for i in cv) + \
        ") VALUES (" + \
        ','.join('%(' + i + ')s' for i in cv) + \
        ");"
    # TODO it appears cur.rowcount does not reflect skipped rows from INSERT IGNORE
    # without this we cannot tell if we have reached the end of our polling
    cur = db.execute("SELECT id FROM checkins WHERE id = %(id)s;", {'id': cx['id']})
    if (cur.fetchone()):
        return 0
    cur = db.execute(sqlCheckin, {
        'id': cx['id'],
        'user_id': user_id,
        'type': cx['type'],
        'timeZoneOffset': cx['timeZoneOffset'],
        'createdAt': cx['createdAt'],
        'private': cx.get('private', 0),
        'shout':  cx['shout'] if cx.get('shout') else None,
        'venue_id': cx['venue']['id'] if cx.get('venue') else None,
        'venue_name': cx['venue']['name'] if cx.get('venue') else None,
        'location': json.dumps(cx['location']) if cx.get('location') else None,
        'event': cx['event']['name'] if cx.get('event') else None,
        'photos': json.dumps(cx['photos']['items']) if cx['photos']['count'] > 0 else None,
        'like': 1 if cx['like'] else 0,
        'post': "\n".join(x['text'] for x in cx['posts']['items']) if cx['posts']['count'] > 0 else None,
        })
    if cx.get('venue'):
        vx = cx['venue'];
        lx = vx['location'];
        cur2 = db.execute(sqlVenue, {
            'id': vx['id'],
            'name': vx['name'],
            'location_address': lx['address'] if lx.get('address') else None,
            'location_crossStreet': lx['crossStreet'] if lx.get('crossStreet') else None,
            'location_lat': lx['lat'],
            'location_lng': lx['lng'],
            'location_postalCode': lx['postalCode'] if lx.get('postalCode') else None,
            'location_cc': lx['cc'] if lx.get('cc') else None,
            'location_city': lx['city'] if lx.get('city') else None,
            'location_state': lx['state'] if lx.get('state') else None,
            'location_country': lx['country'] if lx.get('country') else None,
            'location_formattedAddress': "\n".join(lx['formattedAddress']) if lx.get('formattedAddress') else None,
            'categories': ','.join(x['name'] for x in vx['categories']) if vx.get('categories') else None,
            'closed': 1 if vx.get('closed') else 0,
        })
    return cur.rowcount

def checkins(user_id, *opts):
    #print(user_id)
    sql = "SELECT auth_token FROM users WHERE id = %(id)s;"
    cur = db.execute(sql, {'id': user_id})
    row = cur.fetchone()
    access_token = row[0]
    #print(access_token)
    #print(access_token)
    #client = foursquare.Foursquare(access_token)
    client.set_access_token(access_token)

    #sql = "SELECT MAX(createdAt) FROM checkins WHERE user_id = %(user_id)s;"
    #cur = db.execute(sql, {'user_id': user_id})
    #row = cur.fetchone()
    #after = None
    #if row[0]:
    #    after = row[0] # - 360 # subtract 5mins

    # https://developer.foursquare.com/docs/api/users/checkins
    # afterTimestamp param appears to be ignored!
    limit = 100
    params={'limit': limit, 'sort': 'newestfirst'}
    if len(opts) == 1:
        params['beforeTimestamp'] = opts[0] + 60 # 60s buffer
    recs = client.users.checkins('self', params) #={'limit': limit, 'sort': 'newestfirst'})
    count = 0
    for cx in recs['checkins']['items']:
        #print(cx)
        count += insert_checkin(cx, user_id)
        db.commit()
    print("Inserted "+str(count)) # todo text format
    if count == limit:
        # do another round using beforeTimestamp
        # TODO: sleep, or prevent deep recursion?
        checkins(user_id, cx['createdAt'])
    elif count == 0:
        sys.exit(2)

def all_checkins(user_id):
    sql = "SELECT auth_token FROM users WHERE id = %(id)s;"
    cur = db.execute(sql, {'id': user_id})
    row = cur.fetchone()
    access_token = row[0]
    #print(access_token)
    #client = foursquare.Foursquare(access_token)
    client.set_access_token(access_token)

    recs = client.users.all_checkins() # iteratorable
    #print(recs)
    count = 0
    for cx in recs:
        #print(cx);
        count += insert_checkin(cx, user_id)
    db.commit()
    print("Inserted "+str(count)) # todo text format


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser(description="Download Foursquare Checkins")
parser.add_argument('cmds', metavar="CMD", type=str, nargs='+',
                    help="""auth, auth_redirect, checkins, all_checkins""")

if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

if args.cmds[0] == 'auth':
    auth();
elif args.cmds[0] == 'auth_redirect':
    if len(args.cmds) < 2:
        print("Auth CODE required")
        sys.exit(1)
    auth_redirect(args.cmds[1]);
elif args.cmds[0] == 'checkins':
    if len(args.cmds) < 2:
        print("User ID required")
        sys.exit(1)
    checkins(args.cmds[1])
elif args.cmds[0] == 'all_checkins':
    if len(args.cmds) < 2:
        print("User ID required")
        sys.exit(1)
    all_checkins(args.cmds[1])
else:
    print("instructions...")

