+++
title = "Breaking Software and Getting Older"
date = 2021-12-09T08:10:55+05:30
type = "post"
description = "Rants on why software keeps breaking so often"
in_search_index = true
[taxonomies]
tags = ["Rant"]
+++

Recently, I'd posted on Twitter that my feed has become _messy_ overtime. Maybe I followed some accounts that were of no interest, maybe Twitter's algos don't really know what to show to me. Whatever, I wanted a fresh start. And, I've done this in past. I've removed all the accounts that I follow but they don't follow me back. This little trick is helpful to start afresh while still not offending your friends ;)

![image](/images/twitter_cleanup.png)

I'd written a really simple Python script to do the job! It looks like:

```python
import tweepy

SCREEN_NAME = 'mrkaran_'
CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

followers = api.followers_ids(SCREEN_NAME)
friends = api.friends_ids(SCREEN_NAME)

for f in friends:
    if f not in followers:
        print("Unfollow {0}?".format(api.get_user(f).screen_name))
        api.destroy_friendship(f)
```

I'd last ran this in 2019 or so. That is dinosaur ages in the world of software. All I wanted to do was run this goddamn script again, 2 years later. Seems to be too much of an ask? Apparently `tweepy` the library used here to interact with Twitter's APIs had a [major release](https://github.com/tweepy/tweepy/releases/tag/v4.0.0) with lots of breaking changes. They've internally migrated to start using v2 Twitter API. So, when I naively ran `pip install tweepy`, my code threw:

```python
❯ python main.py    
Traceback (most recent call last):
  File "/home/karan/Code/Personal/twitter-unfollow/main.py", line 13, in <module>
    followers = api.followers_ids(SCREEN_NAME)
AttributeError: 'API' object has no attribute 'followers_ids'
```

So, some method name changed. But that's not all. The whole auth process including the initialisation of the API object changed as well. I'd spent some ~15 minutes grokking the docs but frustrated because 1) I don't give a shit about v2/v1 APIs. 2) I just want to _carry_ on with whatever I was doing. Why is this shit taking more time than I can care to give this to?

I'd have cared enough if it was a side-project I maintained or something that I used daily. A utility like this which gets used once in a couple of years, **will** see more such breaking changes in future. Why, then should I spend migrating to v2 APIs, when after 2 years, v3 APIs would have broken my code again? What is the damn point? Why can't software just keep working without troubling their users?

In the end, I just installed the last version that works with `v1` APIs and ran the script.

I get breaking changes, I totally do. And I've no qualms with Tweepy. They did what they had to, in order to be compatible with v2. I am just angry/sad at the whole ecosystem of "Move fast, break things".

_Please. Slow. Down._

So that the rest of us who have a life can enjoy it and not spend an entire weekend migrating across versions!

Sigh
