from itertools import count
import sys
from time import sleep
from configparser import ConfigParser
import tweepy
import redis
from datetime import datetime, timedelta

#======================
class TweetContext:
    def __init__(self, tweetid, text, userid, name, username,):
        self.tweetid = tweetid
        self.text = text
        self.userid = userid
        self.name = name
        self.username = username
    
    def __str__(self) -> str:
        return "tweetid: %s\nuserid: %s\nname: %s\nusername: %s\ntext: %s\n"%(self.tweetid, self.userid, self.name, self.username, self.text)

def filter_keywords(key_words, text):
    return sum([1 if w in text and w else 0 for w in key_words.split(',')])

def main(argv=None):
    # read config 
    conf = ConfigParser()
    conf.read('config.ini', encoding='utf-8')

    api_key = conf['auth']['api_key']
    api_sec = conf['auth']['api_sec']
    access_token = conf['auth']['access_token']
    access_sec = conf['auth']['access_sec']

    sleep_seconds = conf.getint('service', 'sleep_seconds')
    key_words = conf['service']['key_words']
    quote_context = conf['service']['quote_context']

    conf.read('config.ini', encoding='utf-8')
    chost = conf['redis']['host']
    cport = conf.getint('redis', 'port')
    cdb = conf.getint('redis', 'db')
    cpwd = conf['redis']['passwd']
    ues_redis = conf.getboolean('redis', 'use_redis')

    print('********** config **********')
    print('key_words:', key_words)
    print('ues_redis:', ues_redis)
    print('quote_context:', quote_context)

    # connetc redis
    rds = redis.StrictRedis(host=chost, port=cport, db=cdb, password=cpwd)

    # auth client
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_sec,
        access_token=access_token,
        access_token_secret=access_sec
    )


    totle_find_count = 0
    # Deduplication.
    done_dict = {}
    record_time = datetime.utcnow() - timedelta(days=1)

    # main loop: sleep(sleep_seconds)
    while True:
        print("**************************")
        print('Do new process....')

        if ues_redis:
            b_last_time = rds.get('latest_search')
            str_last_time = b_last_time.decode('utf-8')
            f_last_time = float(str_last_time)
            last_datetime = datetime.fromtimestamp(f_last_time)
        else:
            last_datetime = record_time
        req = client.get_home_timeline(max_results=20,
                                        tweet_fields= ['text', 'id', 'author_id'], 
                                        start_time = last_datetime
                                        #user_fields = "username",
                                        #expansions=['author_id', 'entities.mentions.username']
        )
        if ues_redis:
            rds.set('latest_search', datetime.utcnow().timestamp())
        else:
            record_time = datetime.utcnow()
        
        count = req.meta["result_count"]
        tweets = req.data
        print("time(UTC):", datetime.now())
        print("find tweets in this process: " + str(count))
        print('totle filtered count:', totle_find_count)
        for i in range(0,count):
            print("------------------> ")
            # get user info
            user_info = client.get_user(id=tweets[i].author_id, user_auth=True)

            # twitter info
            # tw_info = client.get_tweet(tweets[i].id, user_auth=True)

            tweet = TweetContext(tweets[i].id, tweets[i].text, user_info.data.id, user_info.data.name, user_info.data.username)
            print(str(tweet))

            # filter key words: RT & like & tag......
            filter_pass = False
            find_count = filter_keywords(key_words, tweet.text.lower())
            print("key world count:", find_count)
            if ues_redis: # deduplicate use redis
                if find_count >= 3 and not rds.sismember('tweet_done',tweet.tweetid ) :
                    filter_pass = True
            else: # deduplicate use dict
                if find_count >= 3 and not tweet.tweetid in done_dict:
                    filter_pass = True

            # do RT & like
            # TODO: find RT user and follow
            if filter_pass:
                print("### find tw:", tweet.tweetid)
                client.like(tweet_id=tweet.tweetid)
                client.retweet(tweet_id=tweet.tweetid)
                client.create_tweet(text=quote_context, 
                                    quote_tweet_id=tweet.tweetid, 
                                    user_auth=True)
                client.follow_user(tweet.userid, user_auth=True)
                done_dict[tweet.tweetid] = True
                if ues_redis:
                    rds.sadd('tweet_done', tweet.tweetid)
                totle_find_count += 1
        
        sleep(sleep_seconds)

if __name__ == "__main__":
    sys.exit(main())