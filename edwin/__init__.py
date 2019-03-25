import eventlet

eventlet.monkey_patch()

import time
from datetime import datetime, timedelta, timezone
import pytz
from email.utils import parsedate_tz
import json
from flask import Flask, request, render_template
from threading import Thread

from tweepy import OAuthHandler, API, Stream, Cursor
from flask_socketio import (
    SocketIO,
    emit,
    join_room,
    leave_room,
    close_room,
    rooms,
    disconnect,
)

from darksky import forecast




socketio = SocketIO()
thread = None

from edwin.tweets import StdOutListener


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")
    app.config["SECRET_KEY"] = "secret!"
    with app.app_context():

        socketio.init_app(app, async_mode="eventlet")

        CONSUMER_KEY = app.config["TWITTER_CONSUMER_KEY"]
        CONSUMER_SECRET = app.config["TWITTER_CONSUMER_SECRET"]
        ACCESS_TOKEN = app.config["TWITTER_ACCESS_TOKEN"]
        ACCESS_TOKEN_SECRET = app.config["TWITTER_ACCESS_TOKEN_SECRET"]
        TWITTER_SCREEN_NAME = app.config["TWITTER_SCREEN_NAME"]

        DARKSKY_KEY = app.config["DARKSKY_KEY"]

        # These config variables come from 'config.py'
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        ids = api.friends_ids(screen_name=TWITTER_SCREEN_NAME, stringify_ids="true")

        try:
            dc = forecast(DARKSKY_KEY, 38.9159, -77.0446)
        
        except:
            pass   

        @app.route("/", methods=["GET"])
        def index():
            global thread
            if thread is None:
                thread = Thread(target=twitter_thread)
                thread2 = Thread(target=darksky_thread)
                thread.daemon = True
                thread.start()
                thread2.start()
            return render_template("index.html")
   
        def twitter_thread():
            """Example of how to send server generated events to clients."""
            stream = Stream(auth, listener)
            _follow = ["15736341", "1"]
            stream.filter(follow=ids, filter_level="low")

        def darksky_thread():
            while True:
                try:
                    dc.refresh(extend='daily')
                except:
                    print("break")
                    break
                sunrise = convert_unix_ts(dc['daily']['data'][0]['sunriseTime'])
                sunset = convert_unix_ts(dc['daily']['data'][0]['sunsetTime'])
                socketio.emit(
                            "darksky_channel",
                            {"temp": int(dc.temperature),
                            "sunrise": sunrise,
                            "sunset": sunset},
                            namespace="/darksky_streaming",
                        )
                time.sleep(120)

            

        listener = StdOutListener()

        return app

def convert_unix_ts(ts):
    ts= int(ts)
    return datetime.fromtimestamp(ts).strftime('%-I:%M:%S')