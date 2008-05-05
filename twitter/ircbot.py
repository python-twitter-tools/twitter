
import time
from dateutil.parser import parse

try:
    import irclib
except:
    raise Exception("This module requires python_irclib")

class SchedTask(object):
    def __init__(self, task, delta):
        self.task = task
        self.delta = delta
        self.next = time.time() + delta
        
class Scheduler(object):
    def __init__(self, tasks):
        self.tasks = sorted(tasks, lambda x,y: cmp(x.delta, y.delta))
    
    def next_task(self):
        now = time.time()
        task = self.tasks.pop(0)
        wait = task.next - now
        if (wait > 0):
            time.sleep(wait)
        task.task()
        task.next = now + task.delta
        for idx in range(len(self.tasks)):
            if self.tasks[idx].next > task.next:
                break
        self.tasks.insert(idx, task)
        
    def run_forever(self):
        try:
            while True:
                self.next_task()
        except KeyboardInterrupt:
            pass
            
class TwitterBot(object):
    def __init__(self, twitter, twitter_users, server, port, nick):
        self.server = server
        self.port = port
        self.nick = nick
        self.twitter = twitter
        self.twitter_user_dict = {}
        now = time.gmtime()
        for user in twitter_users:
            self.twitter_user_dict[user] = now
        self.irc = irclib.IRC()
        self.server = self.irc.server()
        self.sched = Scheduler(
            (SchedTask(self.check_statuses, 60),))

    def check_statuses(self):
        for user, last_update in self.twiter_users.items():
            updates = self.twitter.statuses.user_timeline(
                id=user, count=1)
            if (updates):
                latest = updates[0]
                crt = parse(latest['created_at']).utctimetuple()
                if (crt > last_update):
                    self.server.
                    self.twitter_user_dict[user] = crt
    def run(self):
        self.server.connect(server, port, nick)
        self.server.join(self.channel)
        self.sched.run_forever()

