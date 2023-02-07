# -*- coding: utf-8 -*-
from __future__ import print_function

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.connection import SocketTimeout, ConnectTimeoutError, SocketError, NewConnectionError, connection

import random
from unittest import mock
from config.urls import HOST_IP_MAP

_known_hosts = {}

chose_random_address = True



class LocalResolvAdapter(HTTPAdapter):
    """
    A Adapter for Python Requests that resolves the sets the hostname for certificate
    verification based on the host header.

    This allows requesting the IP address directly via HTTPS without getting
    a "hostname doesn't match" exception.

    """

    def send(self, request, **kwargs):
        with mock.patch(
                "requests.packages.urllib3.connection.HTTPConnection._new_conn",
                _patched_new_conn):
            return super(LocalResolvAdapter, self).send(request, **kwargs)


def _resolve(host):
    addresses = _known_hosts.get(host, None)
    if not addresses:
        return None
    if chose_random_address:
        return random.choice(addresses)
    else:
        return addresses[0]


def register_host(host, addresses):
    """
    Add a new host to the list of known hosts.
    Note that this affects all instances of LocalResolvAdapter.

    :param host: the host name (example.org)
    :type host: str
    :param addresses: the list of ip addresses
    :type addresses: list[str]
    """
    if not isinstance(addresses, list):
        raise RuntimeError("Please specify a list of IP addresses.")
    if host in _known_hosts:
        raise RuntimeError("{} is already known.".format(host))
    _known_hosts[host] = addresses


def deregister_host(host):
    """
    Remove a host from the list of all known hosts.
    Note that this affects all instances of LocalResolvAdapter.

    :param host: the host to remove
    :type host: str
    """
    try:
        del _known_hosts[host]
    except KeyError:
        pass


def _patched_new_conn(self):
    """ Establish a socket connection and set nodelay settings on it.

    This monkey-patched version resolves the host locally and accesses
    the IP address directly.

    :return: New socket connection.
    """

    address = _resolve(self.host)
    if not address:
        raise NewConnectionError(
            self,
            "Failed to establish a new connection: "
            "'{}' couldn't be resolved locally".format(self.host))

    extra_kw = {}
    if self.source_address:
        extra_kw['source_address'] = self.source_address

    if self.socket_options:
        extra_kw['socket_options'] = self.socket_options

    try:
        conn = connection.create_connection(
            (address, self.port), self.timeout, **extra_kw)

    except SocketTimeout as e:
        raise ConnectTimeoutError(
            self, "Connection to %s (%s) timed out. (connect timeout=%s)" %
                  (self.host, address, self.timeout))

    except SocketError as e:
        raise NewConnectionError(
            self, "Failed to establish a new connection: %s" % e)

    return conn


for common_name in HOST_IP_MAP:
    register_host(common_name, HOST_IP_MAP[common_name])
