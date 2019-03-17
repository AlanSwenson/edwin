import eventlet

eventlet.monkey_patch()

import time
from datetime import datetime, timedelta, timezone
import pytz
from email.utils import parsedate_tz
import json
from flask import Flask, request, render_template
from threading import Thread
from tweepy.streaming import StreamListener
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

socketio = SocketIO()
thread = None


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

        # These config variables come from 'config.py'
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        ids = api.friends_ids(screen_name="ashley_begin", stringify_ids="true")

        @app.route("/", methods=["GET"])
        def index():
            global thread
            if thread is None:
                thread = Thread(target=background_thread)
                thread.daemon = True
                thread.start()
            return render_template("index.html")

        class StdOutListener(StreamListener):
            def __init__(self):
                pass

            def on_data(self, data):
                # print(data)
                try:
                    # load json into a dict
                    tweet = json.loads(data)
                    # pull relevent info from the dict
                    text = process_tweet(tweet)

                    # if the tweet meets our criteria, display it in the browser
                    if tweet_is_valid(text):
                        # print(data)
                        socketio.emit(
                            "stream_channel",
                            {"id_str": text["orig_id_str"]},
                            namespace="/demo_streaming",
                        )
                        print("displayed")
                    else:
                        print("skipped")

                except Exception as e:
                    print("passed " + str(e))
                    pass

            def on_error(self, status):
                print("Error status code", status)
                exit()

        def background_thread():
            """Example of how to send server generated events to clients."""
            stream = Stream(auth, listener)
            _keywords = ["codenewbie"]
            _follow = ["15736341", "1"]
            stream.filter(track=_keywords, follow=ids, filter_level="low")

        listener = StdOutListener()

        return app


def process_tweet(tweet):
    retweet = tweet.get("retweeted_status", {})
    actually_created_at = retweet.get("created_at")
    orig_id_str = retweet.get("id_str")
    return {
        "tweet": tweet["text"],
        "created_at": tweet["created_at"],
        "id_str": tweet["id_str"],
        "is_quote_status": tweet["is_quote_status"],
        "in_reply_to_user_id": tweet["in_reply_to_user_id"],
        "actually_created_at": actually_created_at,
        "orig_id_str": orig_id_str,
        # "username": tweet["username"],
        # "headshot_url": t.user.profile_image_url,
    }


def to_datetime(datestring):
    if datestring:
        return datetime.strptime(datestring, "%a %b %d %H:%M:%S +0000 %Y").replace(
            tzinfo=pytz.UTC
        )
    else:
        return None


def tweet_is_valid(text):
    now = datetime.now(timezone.utc)
    # print("datetime of now: " + str(now))
    created_at = to_datetime(text["created_at"])
    # print("datetime of created_at: " + str(created_at))
    actually_created_at = to_datetime(text["actually_created_at"])
    if not actually_created_at:
        return False
    # print("actually created_at: " + str(actually_created_at))
    duration = now - actually_created_at
    duration = duration.total_seconds()
    # print("duration: " + str(duration))
    if (
        duration < 60
        and actually_created_at
        and not text["in_reply_to_user_id"]
        and not text["is_quote_status"]
    ):
        # print(text)
        print(str(text["orig_id_str"]))
        return True
