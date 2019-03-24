import json
from datetime import datetime, timedelta, timezone
import pytz

from tweepy.streaming import StreamListener
#from flask_socketio import SocketIO
from edwin import socketio

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
                        socketio.emit(
                            "tweet_channel",
                            {"id_str": text["orig_id_str"]},
                            namespace="/tweet_streaming",
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
        duration < 600
        and actually_created_at
        and not text["in_reply_to_user_id"]
        and not text["is_quote_status"]
    ):
        # print(text)
        print(str(text["orig_id_str"]))
        return True
