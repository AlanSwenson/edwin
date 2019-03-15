from environs import Env

env = Env()
env.read_env()


TWITTER_CONSUMER_KEY = env.str("consumer_key")
TWITTER_CONSUMER_SECRET = env.str("consumer_secret")
TWITTER_ACCESS_TOKEN = env.str("access_token_key")
TWITTER_ACCESS_TOKEN_SECRET = env.str("access_token_secret")
DEBUG = True

