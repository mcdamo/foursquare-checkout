#!/usr/bin/python3

import sys
from database import Database
import argparse
#import json

import os
from icalendar import Calendar, Event
from datetime import datetime

db = Database()

def export_ics(user_id, path):
    sql = """
SELECT 
c.id,
c.createdAt,
c.timeZoneOffset,
v.location_lat,
v.location_lng,
v.name,
REPLACE(v.location_formattedAddress, '\n', ','),
v.location_country,
c.event,
c.shout,
c.post
FROM checkins c
INNER JOIN venues v ON v.id = c.venue_id
WHERE c.user_id = %(user_id)s
ORDER BY c.createdAt DESC
;"""
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//www.foursquare.com/foursquare ICS//EN')
    cal.add('calscale', 'GREGORIAN') # TODO?
    cal.add('method', 'PUBLISH') # TODO?
    cal.add('x-wr-calname', '4sq-checkout')
    cur = db.execute(sql, {'user_id': user_id});
    dtnow = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    for row in cur:
        event = Event()
        dt = datetime.utcfromtimestamp(row[1]).strftime('%Y%m%dT%H%M%SZ')
        summary = (row[8] + ' ' if row[8] else '') + '@ ' + row[5]
        event['uid'] = row[0] + '@foursquare.com'
        event['dtstart'] = dt
        event['dtend'] = dt
        event['dtstamp'] = dtnow
        event['url'] = 'https://foursquare.com/user/' + user_id + '/checkin/' + row[0]
        if row[3]:
            event['geo'] = ';'.join([row[3], row[4]])
        event['summary'] = summary
        event['description'] = "\n".join(filter(None, [ summary, row[9], row[10] ]))
        event['location'] = ", ".join(filter(None, [ row[5], row[6], row[7] ]))
        cal.add_component(event)
    f = open(path, 'wb')
    f.write(cal.to_ical())
    f.close()

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser(description="Export Foursquare checkins")
parser.add_argument('cmds', metavar="CMD", type=str, nargs='+',
                    help="""USER FILE.ics,...""")

if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

if len(args.cmds) < 2:
    print("input required")
    sys.exit(1)
else:
    export_ics(args.cmds[0], args.cmds[1]);
