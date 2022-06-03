import redis
from configparser import ConfigParser
from datetime import datetime

 # read config 
conf = ConfigParser()
conf.read('config.ini', encoding='utf-8')
chost = conf['redis']['host']
cport = conf.getint('redis', 'port')
cdb = conf.getint('redis', 'db')
cpwd = conf['redis']['passwd']

r = redis.StrictRedis(host=chost, port=cport, db=cdb, password=cpwd)

# done list
r.sadd("tweet_done", '13131312', '123123123123')
r.persist('tweet_done')

# time
now = datetime.utcnow()
r.set('latest_search', now.timestamp())
r.persist('latest_search')
print(now)

# test
print(r.ttl('tweet_done'))
print(r.sismember('tweet_done', "123123123123"))
print(r.sismember('tweet_done', "123"))