#!/usr/bin/env python
# coding: utf-8


from __future__ import print_function
from __future__ import unicode_literals
from opsview import Opsview
from rdpy.protocol.rdp import rdp
from rdpy.protocol.rfb import rfb
from twisted.internet import reactor
import argparse
import logging
import paramiko
import rdpy.core.log as rdpylog
import shortmomi
import sys


rdpylog._LOG_LEVEL = rdpylog.Level.NONE
logging.basicConfig()
logger = logging.getLogger(__name__)


class MyVNCFactory(rfb.ClientFactory):
    def __init__(self, password=None, timeout=10):
        self._password = password
        self._timeout = timeout
        self._success = False

    def clientConnectionLost(self, connector, reason):
        logger.info('Connection lost')
        # If the connection failed, then there is no need to stop reactor
        if not self._success:
            reactor.crash()

    def buildObserver(self, controller, addr):
        if self._password:
            controller.setPassword(self._password)

        return SimpleVNCObserver(
            self, reactor, timeout=self._timeout, controller=controller
        )


class SimpleVNCObserver(rfb.RFBClientObserver):
    def __init__(self, factory, reactor, controller, timeout=10):
        self._factory = factory
        self._reactor = reactor
        self._startTimeout = False
        self._timeout = timeout
        super(self.__class__, self).__init__(controller)

    def onUpdate(self, width, height, x, y, pixelFormat, encoding, data):
        print('UPDATE')
        if not self._startTimeout:
            self._startTimeout = False
            self._reactor.callLater(self._timeout, self.terminate)

    def terminate(self):
        self._controller.close()

    def onReady(self):
        self._factory._success = True
        self.terminate()

    def onBell(self):
        pass

    def onCutText(self):
        pass

    def onClose(self):
        pass


class MyRDPFactory(rdp.ClientFactory):

    def __init__(self, username, password, domain, timeout=10):
        self._username = username
        self._password = password
        self._domain = domain
        self._success = False
        self._timeout = timeout

    def clientConnectionLost(self, connector, reason):
        logger.info('Connection lost')
        # If the connection failed, then there is no need to stop reactor
        if not self._success:
            reactor.crash()


    def clientConnectionFailed(self, connector, reason):
        logger.info('Connection failed')
        reactor.crash()

    def buildObserver(self, controller, addr):
        controller.setUsername(self._username)
        controller.setPassword(self._password)
        if self._domain:
            controller.setDomain(self._domain)

        return SimpleRDPObserver(
            self, reactor, timeout=self._timeout, controller=controller
        )


class SimpleRDPObserver(rdp.RDPClientObserver):
    def __init__(self, factory, reactor, controller, timeout=10):
        self._factory = factory
        self._reactor = reactor
        self._startTimeout = False
        self._timeout = timeout
        super(self.__class__, self).__init__(controller)

    def onUpdate(self, destLeft, destTop, destRight, destBottom, width, height,
                 bitsPerPixel, isCompress, data):
        if not self._startTimeout:
            self._startTimeout = False
            self._reactor.callLater(self._timeout, self.terminate)

    def terminate(self):
        self._controller.close()
        self._reactor.crash()

    def onReady(self):
        pass

    def onSessionReady(self):
        self._factory._success = True
        self.terminate()

    def onClose(self):
        pass


def ssh_connection(hostname, username, password, port=22, timeout=10):
    try:
        ssh = paramiko.SSHClient()
        # Automatically add new hosts keys
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Connection
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            timeout=timeout
        )
        logger.info('SSH {}@{}: Login succeeded'.format(username, hostname))
        return True
    except:
        logger.error(
            'SSH {}@{}: Login failed! Password: {}'.format(
                username, hostname, password
            )
        )
    return False


def vnc_connection(hostname, password=None, port=5900, timeout=10):
    r = reactor.connectTCP(hostname, port, MyVNCFactory(password, timeout))
    if not reactor.running:
        reactor.run()
    return r.factory._success


def rdp_connection(hostname, username, password, domain=None, port=3389,
                   timeout=10):
    r = reactor.connectTCP(
        hostname, port, MyRDPFactory(
            username, password, domain, timeout
        )
    )
    if not reactor.running:
        reactor.run()
    return r.factory._success


def vcenter_connection(hostname, username, password, domain=None, port=443,
                       verify=True):
    try:
        user = '{}@{}'.format(username, domain) if domain else username
        shortmomi.connect(hostname, user, password, verify=verify)
        return True
    except shortmomi.ConnectionError:
        logger.error(
            'Could not login using {}:{} on the vCenter at {}'.format(
                username, password, hostname
            )
        )
    return False


def opsview_connection(hostname, username, password, port=443, verify=True):
    try:
        ops = Opsview(
            hostname,
            username=username,
            password=password,
            verify_ssl=verify
        )
        ops.user_info()
        return True
    except AssertionError:
        pass
    return False


def parse_args():
    parser = argparse.ArgumentParser()
    protocol_subparsers = parser.add_subparsers(
        title='protocol',
        dest='protocol',
        help='Supported protocols'
    )
    ssh_subparser = protocol_subparsers.add_parser(
        'ssh',
        help='SSH connection'
    )
    ssh_subparser.add_argument(
        '-u', '--username',
        default='root',
        required=False
    )
    ssh_subparser.add_argument(
        '-p', '--password'
    )
    ssh_subparser.add_argument(
        '-P', '--port',
        type=int,
        default=22,
        required=False
    )
    ssh_subparser.add_argument(
        '-t', '--timeout',
        type=int,
        default=10,
        required=False
    )
    ssh_subparser.add_argument('HOSTNAME')
    rdp_subparser = protocol_subparsers.add_parser(
        'rdp',
        help='RDP connection'
    )
    rdp_subparser.add_argument(
        '-u', '--username',
        default='Administrator',
        required=False
    )
    rdp_subparser.add_argument(
        '-p', '--password'
    )
    rdp_subparser.add_argument(
        '-d', '--domain',
        required=False
    )
    rdp_subparser.add_argument(
        '-P', '--port',
        type=int,
        default=3389,
        required=False
    )
    rdp_subparser.add_argument(
        '-t', '--timeout',
        type=int,
        default=10,
        required=False
    )
    rdp_subparser.add_argument('HOSTNAME')
    vnc_subparser = protocol_subparsers.add_parser(
        'vnc',
        help='VNC connection'
    )
    vnc_subparser.add_argument(
        '-p', '--password',
        required=False
    )
    vnc_subparser.add_argument(
        '-P', '--port',
        type=int,
        default=5900,
        required=False
    )
    vnc_subparser.add_argument(
        '-t', '--timeout',
        type=int,
        default=10,
        required=False
    )
    vnc_subparser.add_argument('HOSTNAME')
    vcenter_subparser = protocol_subparsers.add_parser(
        'vcenter',
        help='VMware vCenter connection'
    )
    vcenter_subparser.add_argument(
        '-u', '--username',
        default='administrator',
        required=False
    )
    vcenter_subparser.add_argument(
        '-p', '--password'
    )
    vcenter_subparser.add_argument(
        '-d', '--domain',
        help='Domain (realm)',
        default='vsphere.local',
        required=False
    )
    vcenter_subparser.add_argument(
        '-k', '--skip-cert-verification',
    )
    vcenter_subparser.add_argument(
        '-P', '--port',
        type=int,
        default=443,
        required=False
    )
    opsview_subparser = protocol_subparsers.add_parser(
        'opsview',
        help='Opsview connection'
    )
    opsview_subparser.add_argument(
        '-k', '--skip-cert-verification',
    )
    opsview_subparser.add_argument(
        '-u', '--username',
    )
    opsview_subparser.add_argument(
        '-p', '--password'
    )
    opsview_subparser.add_argument(
        '-P', '--port',
        type=int,
        default=443,
        required=False
    )
    opsview_subparser.add_argument('HOSTNAME')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.protocol == 'ssh':
        result = ssh_connection(
            hostname=args.HOSTNAME,
            username=args.username,
            password=args.password,
            port=args.port,
            timeout=args.timeout
        )
    elif args.protocol == 'rdp':
        result = rdp_connection(
            hostname=args.HOSTNAME,
            domain=args.domain,
            username=args.username,
            password=args.password,
            port=args.port,
            timeout=args.timeout
        )
    elif args.protocol == 'vnc':
        result = vnc_connection(
            hostname=args.HOSTNAME,
            password=args.password,
            port=args.port,
            timeout=args.timeout
        )
    elif args.protocol == 'vcenter':
        result = vcenter_connection(
            hostname=args.HOSTNAME,
            domain=args.domain,
            username=args.username,
            password=args.password,
            port=args.port,
            verify=not args.skip_ssl_verification
        )
    elif args.protocol == 'opsview':
        result = opsview_connection(
            hostname=args.HOSTNAME,
            domain=args.domain,
            username=args.username,
            password=args.password,
            port=args.port,
            verify=not args.skip_ssl_verification
        )

    if result:
        print('Connection succeesfully established!')
    else:
        print('Connection FAILED', file=sys.stderr)

if __name__ == '__main__':
    main()
