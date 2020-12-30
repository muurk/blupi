import queue
import threading
import logging
import time

class Message(object):
    def __init__(self, body, title="Message", data="", priority=10):
        self.priority = priority
        self.title = title
        self.body = body

        return

    def __cmd__(self, priority):
        return cmp(self.priority, other.priority)

class BaseAlert(object):
    def __init__(self):
        self.refresh_time = float() 
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        #self.queue = queue.PriorityQueue()
        self.queue = queue.Queue()
        self.ready()
        self.start()
        self.update_refresh_time() 

    def update_refresh_time(self):
        self.refresh_time = time.time()

    def message(self, **kwargs):
        try:
            m = Message(**kwargs)
            self.queue.put(m)
        except:
            self.log.error("Failed to add message to queue")
            self.log.error(m)

    def clear(self):
        pass

    def info(self, message):
        pass

    def warning(self, message):
        pass

    def queue_monitor(self):
        while True:
            self.refresh_display()
            try:
                # pass
                task = self.queue.get_nowait()
                #task = self.queue.get(block=False)
                self.refresh_time = time.time()
                self.display_message(task)
            except:
                pass

        self.refresh_display()

    def start(self):
        self.log.debug("Starting Alert Queue")
        thread = threading.Thread(target=self.queue_monitor)
        #thread.setDaemon(True)
        thread.start()
        #thread.join()
        self.log.debug("Alert Queue Running")

    def refresh_display(self):
        if time.time() - self.refresh_time >= 60:
            self.ready() 
            self.refresh_time = time.time()
