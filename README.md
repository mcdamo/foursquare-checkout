# Foursquare-Checkout

## What is this?

This is a simple script to extract your Foursquare Checkins to a local database. This may be for a personal backup or for easy generation of other formats such as ICS or KML.

Foursquare used to provide [feeds](https://foursquare.com/feeds/) for personal checkins in RSS, KML, and ICS formats. Sadly in early 2019 these feeds were abandoned by Foursquare and many users report they no longer work.

One of the included scripts will generate a ICS calendar file in a similar format to what Foursquare used to provide.

## Dependencies

- MariaDB or MySQL for a local database

- Foursquare library: [pypi](https://pypi.python.org/pypi/foursquare) [github](https://github.com/mLewisLogic/foursquare)

- iCalendar library: [pypi](https://pypi.org/project/icalendar/) [github](https://github.com/collective/icalendar/)

(Note: [ics](https://pypi.org/project/ics/) is potential alternative calendar library but it doesn't appear to support the GEO field)

## Prerequisites

You will need to sign up for a free [Foursquare Developer](https://developer.foursquare.com/) account and create your own Client APP with permission to use the *Places API*. In creating a Client you will be asked to set an *Application URL* and *Redirect URL* - this app does not need them, but they are required to be set to allow for the initial authentication.

## Install

- Install virtual-env

  `python3 -m venv venv`

  `source venv/bin/activate`

- Install the dependencies: Foursquare API library `foursquare` and optionally the iCalendar library to enable ICS export `icalendar`

  `pip3 install -r requirements.txt`

- Create your database with the provided *schema.sql*.

- Create *config.ini* and fill in the database details and your Foursquare Client details from your developer account.

## Authentication

Authentication only needs to be done once per user. Once a user is authenticated a token is stored in the local database and this token remains valid indefinitely.

Run the auth command to generate an authentication request

```
./foursquare-api.py auth

https://foursquare.com/oauth2/authenticate?client_id=...
```

Open the printed link in your browser to grant access to this app from your own Foursquare account. This will generate a code in return.

Run the next command with the returned auth code

`./foursquare-api.py auth_redirect <CODE>`

A user will be inserted in the local database with a token to grant access to checkins.

## Usage

Commands:

- *checkins*: fetch most recent 100 checkins and insert into database.
- *all_checkins*: fetch ALL checkins and insert into database (this may take a while).

### Download Checkins

The *USER_ID* will be listed in the *users* table after authentication.

`./foursquare-api.py checkins <USER_ID>`

### Export ICS

`./ics_export.py <USER_ID> <FILE.ICS>`

## Further info

- [Foursquare Checkins API](https://developer.foursquare.com/docs/api/users/checkins)


## TODO
- add sqlite database support
- streamline database creation
- streamline authentication (requires a webserver to handle redirect)
- define ICS template in a config file
- add support for exporting as KML
