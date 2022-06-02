from itertools import count
import sys
from time import sleep
from configparser import ConfigParser
import tweepy

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

    auths = conf['auth']
    api_key = auths['api_key']
    api_sec = auths['api_sec']
    access_token = auths['access_token']
    access_sec = auths['access_sec']

    items = conf['item']
    sleep_seconds = conf.getint('item', 'sleep_seconds')
    key_words = items['key_words']

    # auth client
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_sec,
        access_token=access_token,
        access_token_secret=access_sec
    )

    totle_find_count = 0
    # Deduplication. TODO: use redis
    done_dict = {}

    # main loop: sleep(sleep_seconds)
    while True:
        print("**************************")
        print('totle finded count:', totle_find_count)
        print('Do new process....')

        req = client.get_home_timeline(max_results=20,
                                        tweet_fields= ['text', 'id', 'author_id'], 
                                        #user_fields = "username",
                                        expansions=['author_id', 'entities.mentions.username'])
        count = req.meta["result_count"]
        tweets = req.data
        users = req.includes['users']
        print("find tweets in this process: " + str(count))

        for i in range(0,count):
            print("------------------> ")
            # get user info
            user_info = client.get_user(id=tweets[i].author_id, user_auth=True)
            # print("userinfo:", user_info)

            # twitter info
            # tw_info = client.get_tweet(tweets[i].id, user_auth=True)
            # print("tw:", tw_info)

            tweet = TweetContext(tweets[i].id, tweets[i].text, user_info.data.id, user_info.data.name, user_info.data.username)
            print(str(tweet))

            # filter key words: RT & like & tag......
            filter_pass = False
            count = filter_keywords(key_words, tweet.text.lower())
            print("key world count:", count)
            if count > 2:
                filter_pass = True

            # do RT & like
            # TODO: find RT user and follow
            if filter_pass and not tweet.tweetid in done_dict:
                print("### find tw:", tweet.tweetid)
                client.like(tweet_id=tweet.tweetid)
                client.retweet(tweet_id=tweet.tweetid)
                client.create_tweet(text='Nice project! @webbergao1 @Deparetos @Mark_XZZ', 
                                    quote_tweet_id=tweet.tweetid, 
                                    user_auth=True)
                client.follow_user(tweet.userid, user_auth=True)
                done_dict[tweet.tweetid] = True
                totle_find_count += 1
        
        sleep(sleep_seconds)

if __name__ == "__main__":
    sys.exit(main())