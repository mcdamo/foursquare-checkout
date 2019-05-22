#!/usr/bin/python3

import sys
from database import Database
import argparse
#import json

import os
from icalendar import Calendar, Event, vDatetime
from datetime import datetime
import pytz

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
    #dtnow = datetime.now(timezone.utc) # this returns TZ aware datetime. utcnow() is TZ naive
    dtnow = datetime.utcnow().replace(tzinfo=pytz.utc)
    for row in cur:
        event = Event()
        dt = datetime.utcfromtimestamp(row[1]).replace(tzinfo=pytz.utc)
        summary = (row[8] + ' ' if row[8] else '') + '@ ' + row[5]
        event.add('uid', row[0] + '@foursquare.com')
        #event.add('dtstart', dt )
        #event.add('dtend', dt )
        #event.add('dtstamp', dt )
        event['dtstart'] = vDatetime(dt).to_ical()
        event['dtend'] = vDatetime(dt).to_ical()
        event['dtstamp'] = vDatetime(dtnow).to_ical()
        event.add('url', 'https://foursquare.com/user/' + user_id + '/checkin/' + row[0])
        if row[3]:
            event.add('geo', (float(row[3]), float(row[4])))
        event.add('summary', summary)
        event.add('description', "\n".join(filter(None, [ summary, row[9], row[10] ])) )
        event.add('location', ", ".join(filter(None, [ row[5], row[6], row[7] ])) )
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
