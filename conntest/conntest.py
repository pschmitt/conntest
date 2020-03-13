#!/usr/bin/env python
# coding: utf-8


from __future__ import print_function
from __future__ import unicode_literals
import argparse
import logging
import paramiko
import shortmomi
import sys


LOGGER = logging.getLogger(__name__)


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
            timeout=timeout,
        )
        LOGGER.info("SSH {}@{}: Login succeeded".format(username, hostname))
        return True
    except:
        LOGGER.error(
            "SSH {}@{}: Login failed! Password: {}".format(
                username, hostname, password
            )
        )
    return False


def vcenter_connection(
    hostname, username, password, domain=None, port=443, verify=True
):
    try:
        user = "{}@{}".format(username, domain) if domain else username
        shortmomi.connect(hostname, user, password, verify=verify)
        return True
    except shortmomi.ConnectionError:
        LOGGER.error(
            "Could not login using {}:{} on the vCenter at {}".format(
                username, password, hostname
            )
        )
    return False


def parse_args():
    parser = argparse.ArgumentParser()
    protocol_subparsers = parser.add_subparsers(
        title="protocol", dest="protocol", help="Supported protocols"
    )
    ssh_subparser = protocol_subparsers.add_parser("ssh", help="SSH connection")
    ssh_subparser.add_argument(
        "-u", "--username", default="root", required=False
    )
    ssh_subparser.add_argument("-p", "--password")
    ssh_subparser.add_argument(
        "-P", "--port", type=int, default=22, required=False
    )
    ssh_subparser.add_argument(
        "-t", "--timeout", type=int, default=10, required=False
    )
    ssh_subparser.add_argument("HOSTNAME")
    vcenter_subparser = protocol_subparsers.add_parser(
        "vcenter", help="VMware vCenter connection"
    )
    vcenter_subparser.add_argument(
        "-u", "--username", default="administrator", required=False
    )
    vcenter_subparser.add_argument("-p", "--password")
    vcenter_subparser.add_argument(
        "-d",
        "--domain",
        help="Domain (realm)",
        default="vsphere.local",
        required=False,
    )
    vcenter_subparser.add_argument(
        "-k", "--skip-cert-verification",
    )
    vcenter_subparser.add_argument(
        "-P", "--port", type=int, default=443, required=False
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.protocol == "ssh":
        result = ssh_connection(
            hostname=args.HOSTNAME,
            username=args.username,
            password=args.password,
            port=args.port,
            timeout=args.timeout,
        )
    elif args.protocol == "vcenter":
        result = vcenter_connection(
            hostname=args.HOSTNAME,
            domain=args.domain,
            username=args.username,
            password=args.password,
            port=args.port,
            verify=not args.skip_ssl_verification,
        )

    if result:
        print("Connection succeesfully established!")
    else:
        print("Connection FAILED", file=sys.stderr)


if __name__ == "__main__":
    main()
