from .remote_property import RemoteProperty
from pyhtmlgui import Observable, ObservableList


class CustomPortForwardings(Observable):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.portforwardings = ObservableList()
        self.auto_renew_port_forwarding = RemoteProperty("autorenew_pf", self.queue)
        self.email_port_forwarding_updates = RemoteProperty("emailPortForwarding", self.queue)

    def add(self, servergroup, dst_port ):
        self.queue.put({"setPortForwarding": ["%s,%s" % (servergroup, dst_port)]})

    def add_one_to_one(self, servergroup):
        self.queue.put({"setPortForwarding":[servergroup] } )

    def remove(self, customPortForwarding):
        self.portforwardings.remove(customPortForwarding)
        self.queue.put({"deletePortForwarding": [customPortForwarding.id]})

    def update(self, datas):
        current_ids = [pf.id      for   pf in self.portforwardings]
        new_ids     = [data["id"] for data in datas]
        updated = False
        for current_id in current_ids:
            if current_id not in new_ids:
                self.portforwardings.remove([pf for pf in self.portforwardings if pf.id == current_id][0])
                updated = True
        current_ids = [pf.id      for   pf in self.portforwardings]
        for data in datas:
            if data["id"] not in current_ids:
                updated = True
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