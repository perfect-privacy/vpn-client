import requests, logging, time
from .webrequests_local_resolv_adapter import LocalResolvAdapter

logger = logging.getLogger("webrequests")


DEFAULT_TIMEOUT = 10.0
enable_direct_access = True
lock_until = 0


# Central downloader, container dns workarround and blocks on windows if network state is changeing
class WebRequest:
    @classmethod
    def lock(cls,timeout = 5):
        global lock_until
        lock_until = time.time() + timeout
    @classmethod
    def unlock(cls):
        global lock_until
        lock_until = 0

    def __init__(self, user_agent=""):
        self._ordinary_session = requests.Session()
        self._ordinary_session.headers.update({"User-Agent": user_agent})

        self._local_resolv_session = requests.Session()
        self._local_resolv_session.headers.update({"User-Agent": user_agent})
        adapter = LocalResolvAdapter()
        self._local_resolv_session.mount("http://", adapter)
        self._local_resolv_session.mount('https://', adapter)

    def get(self, url, headers=None, timeout=DEFAULT_TIMEOUT, **kwargs):
        #logger.debug( "requesting (GET): {}, headers: {}, direct access enabled: {}".format(url, headers, enable_direct_access))
        if lock_until > time.time():
            #logger.debug("requesting (GET): {} delayed".format(url))
            while lock_until > time.time():
                time.sleep(0.5)
            #logger.debug("requesting (POST): {} continues".format(url))

        session = self._local_resolv_session if enable_direct_access else self._ordinary_session
        if session is None:
            logger.error("central requester has not been set up yet")
            raise Exception("central requester has not been set up yet")

        return session.get(url, headers=headers, verify=True, timeout=timeout, **kwargs)


    def post(self, url, headers=None, timeout=DEFAULT_TIMEOUT, **kwargs):
        #logger.debug("requesting (POST): {}, headers: {}, direct access enabled: {}".format(url, headers, enable_direct_access))
        if lock_until > time.time():
            #logger.debug("requesting (POST): {} delayed".format(url))
            while lock_until > time.time():
                time.sleep(0.5)
            #logger.debug("requesting (POST): {} continues".format(url))

        session = self._local_resolv_session if enable_direct_access else self._ordinary_session
        if session is None:
            logger.error("central requester has not been set up yet")
            raise Exception("central requester has not been set up yet")

        return session.post(url, headers=headers, verify=True, timeout=timeout, **kwargs)

