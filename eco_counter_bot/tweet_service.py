import logging
import tweepy

from textwrap import wrap

from eco_counter_bot.config import config

logger = logging.getLogger(f"eco_counter_bot.{__name__}")

class TweetService:

    def __init__(self):
        self.api = None
        self.do_authentication(
            config.get("TWITTER_API_KEY"),
            config.get("TWITTER_API_SECRET"),
            config.get("TWITTER_ACCESS_TOKEN"),
            config.get("TWITTER_ACCESS_SECRET")
        )

    def do_authentication(self, consumer_key, consumer_secret, access_token, access_token_secret):
        logger.debug("Setting Twitter authentication")

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def upload_media(self, filename):
        if config.get("DEV"):
            logger.debug("Not uploading media since program is running in development mode")
            return None

        logger.debug(f"Uploading media with filename {filename}")

        return self.api.media_upload(filename=filename)

    def tweet_thread(self, text, lat=None, lon=None, media_filename=None, extra_parts=[], answer_to=None):
        logger.debug("Sending tweet (as thread if necessary)")

        media = None

        if media_filename:
            media = self.upload_media(media_filename)
            logger.debug(f"Uploaded media: {media}")

        parts = [text]

        if len(text) > 280:
            logger.debug("Text longer than 280 chars, wrapping it")
            raw_wrapped = wrap(text, 270, replace_whitespace=False)
            parts = list(map(lambda part_tuple: f"{part_tuple[1]} {part_tuple[0]+1}/{len(raw_wrapped)}", enumerate(raw_wrapped)))

        parts.extend(extra_parts)
        last_status = answer_to
        tweet_ids = []

        for index, part in enumerate(parts):
            logger.debug(f"Tweeting part {index+1}/{len(parts)}")
            tweet_params = { 'status': part }

            if index == 0 and media:
                tweet_params['media_ids'] = [media.media_id]

            if last_status:
                tweet_params['in_reply_to_status_id'] = last_status
                tweet_params['auto_populate_reply_metadata'] = True

            if lat and lon:
                tweet_params['lat'] = lat
                tweet_params['long'] = lon
                tweet_params['display_coordinates'] = True

            logger.debug(f'Tweeting with params: {tweet_params}')

            if config.get("DEV"):
                logger.debug("Not sending tweet since program is running in development mode")
                return ["TWEET_ID1", "TWEET_ID2", "TWEET_ID3"]
            else:
                last_status = self.api.update_status(**tweet_params).id
                tweet_ids.append(last_status)

        return tweet_ids
