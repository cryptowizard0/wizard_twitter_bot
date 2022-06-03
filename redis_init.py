import redis
from configparser import ConfigParser

 # read config 
conf = ConfigParser()
conf.read('config.ini', encoding='utf-8')
chost = conf['redis']['host']
cport = conf.getint('redis', 'port')
cdb = conf.getint('redis', 'db')

r = redis.StrictRedis(host=chost, port=cport, db=cdb)

r.set('latest_search', 0)
#r.persist('latest_search')

# done list
r.sadd("tweet_done", '13131312', '123123123123')
r.persist('tweet_done')


# test
print(r.ttl('tweet_done'))
print(r.sismember('tweet_done', "123123123123"))
print(r.sismember('tweet_done', "123"))