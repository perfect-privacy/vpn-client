from .remote_property import RemoteProperty
from pyhtmlgui import Observable

class TrackStop(Observable):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.block_kids     = RemoteProperty("blockkids", self.queue)
        self.block_ads      = RemoteProperty("blockads", self.queue)
        self.block_fraud    = RemoteProperty("blockfraud", self.queue)
        self.block_fakenews = RemoteProperty("blockfakenews", self.queue)
        self.block_facebook = RemoteProperty("blockfacebook", self.queue)
        self.block_google   = RemoteProperty("blockgoogle", self.queue)
        self.block_social   = RemoteProperty("blocksocial", self.queue)

    def update(self, data):
        self.block_kids.update(data["kids"])
        self.block_ads.update(data["ads"])
        self.block_fraud.update(data["fraud"])
        self.block_fakenews.update(data["fakenews"])
        self.block_facebook.update(data["facebook"])
        self.block_google.update(data["google"])
        self.block_social.update(data["social"])
        self.notify_observers()