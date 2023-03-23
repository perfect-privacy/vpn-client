import random

from .remote_property import RemoteProperty
from pyhtmlgui import Observable, ObservableList


class CustomPortForwardings(Observable):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.portforwardings = ObservableList()

    def add(self, servergroup, dst_port ):
        self.portforwardings.append(CustomPortForwarding(
            id=random.randint(0,2**31),
            serverGroupId=servergroup,
            destPort=dst_port,
            srcPort="",
            validUntil="pending",
            parent=self
        ))
        self.queue.put({"setPortForwarding": ["%s,%s" % (servergroup, dst_port)]})

    def add_one_to_one(self, servergroup):
        self.portforwardings.append(CustomPortForwarding(
            id=random.randint(0,2**31),
            serverGroupId=servergroup,
            destPort="",
            srcPort="",
            validUntil="pending",
            parent=self
        ))
        self.queue.put({"setPortForwarding":[servergroup] } )

    def remove(self, customPortForwarding):
        if customPortForwarding.validUntil == "pending":
            self.portforwardings.remove(customPortForwarding)
            if customPortForwarding.destPort == "":
                self.queue.cancel({"setPortForwarding":[customPortForwarding.serverGroupId] })
            else:
                self.queue.cancel({"setPortForwarding": ["%s,%s" % (customPortForwarding.serverGroupId, customPortForwarding.dstPort)]})
        else:
            customPortForwarding.validUntil = "pending delete"
            customPortForwarding.notify_observers()
            self.queue.put({"deletePortForwarding": [customPortForwarding.id]})

    def update(self, datas):
        current_ids = [pf.id      for   pf in self.portforwardings]
        new_ids     = [data["id"] for data in datas]
        for current_id in current_ids:
            if current_id not in new_ids:
                self.portforwardings.remove([pf for pf in self.portforwardings if pf.id == current_id][0])
        current_ids = [pf.id      for   pf in self.portforwardings]
        for data in datas:
            if data["id"] not in current_ids:
                self.portforwardings.append(CustomPortForwarding(
                    id = data["id"],
                    serverGroupId = data["serverGroupId"],
                    destPort = data["destPort"],
                    srcPort = data["srcPort"],
                    validUntil = data["validUntil"],
                    parent = self
                ))
        self.notify_observers()


    def __len__(self):
        return len(self.portforwardings)



class CustomPortForwarding(Observable):
    def __init__(self, id, serverGroupId, destPort, srcPort, validUntil, parent):
        super().__init__()
        self.id = id
        self.serverGroupId = serverGroupId
        self.dstPort = destPort
        self.srcPort = srcPort
        self.validUntil = validUntil
        self.parent = parent

    def remove(self):
        self.parent.remove(self)