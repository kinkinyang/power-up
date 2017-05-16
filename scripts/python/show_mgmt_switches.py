#!/usr/bin/env python
# Copyright 2017 IBM Corp.
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import nested_scopes, generators, division, absolute_import, \
    with_statement, print_function, unicode_literals

import sys
import os.path
from lib import inventory
from lib.logger import Logger
import netaddr
import subprocess
from lib.ssh import SSH

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class SSH_(SSH):
    SSH_LOG = FILE_PATH + '__ssh.log'


def main(log, inv_file):
    inv = inventory.Inventory(log, inv_file)

    userid = inv.get_userid_mgmt_switch()
    password = inv.get_password_mgmt_switch()

    mgmt_network_port = inv.get_port_mgmt_network()
    mgmt_network_gen = inv.get_ipaddr_mgmt_network()

    mgmt_network_ext = inv.get_mgmt_switch_external_dev_ip()
    mgmt_network_ext_prefix = inv.get_mgmt_switch_external_prefix()
    mgmt_network_ext = mgmt_network_ext + '/' + mgmt_network_ext_prefix

    mgmt_network_ext = netaddr.IPNetwork(mgmt_network_ext)
    mgmt_network_ext_cidr = str(mgmt_network_ext.cidr)

    output = subprocess.check_output(['bash', '-c', 'ip route'])
    if mgmt_network_ext_cidr in output:
        key_addr = 'addr_ext'
    elif mgmt_network_gen in output:
        key_addr = 'addr_gen'
    else:
        sys.exit("No path found to switch.")
    print('==============================')
    print('Defined switches: ')
    n = 1
    switches_m = {}
    for rack, ip in inv.yield_mgmt_rack_ipv4():
        switches_m[n] = {'rack': rack, 'addr_gen': ip}
        n += 1

    n = 1
    for ip in inv.yield_mgmt_switch_external_switch_ip():
        switches_m[n]['addr_ext'] = ip
        print(' ' + str(n) + ')  rack: ' +
              switches_m[n]['rack'] + ',  external address: ' +
              switches_m[n]['addr_ext'] + ',  Genesis address: ' +
              switches_m[n]['addr_gen'])
        n += 1
    if not (len(switches_m) == 1):
        sw = get_int_input("\n\nSelect a switch: ", 1, len(switches_m))
    else:
        sw = 1

    print()
    ssh_i = SSH_(log)
    status, mgmt_interfaces, ssh_err = ssh_i.exec_cmd(
        switches_m[sw][key_addr],
        userid,
        password,
        'show interface ip;')

    print_lines(mgmt_interfaces, ['Interface information:', 'IP4'])

    print()
    status, mgmt_port, ssh_err = ssh_i.exec_cmd(
        switches_m[sw][key_addr],
        userid, password, 'show interface port %s;' % str(mgmt_network_port))

    print_lines(mgmt_port, ['Current port', 'VLANs'])

    status, vlans, ssh_err = ssh_i.exec_cmd(
        switches_m[sw][key_addr], userid, password, 'show vlan;')
    print('\n\nVLAN information: ')
    print_lines(vlans, ['-  ------  -', 'VLAN'])
    print()


def print_lines(str, line_list):
    """Splits str at newline (\n) characters, then prints the lines which
    contain elements from line_list"""
    str = str.splitlines()
    index = 0
    for i in range(len(str)):
        for substr in line_list:
            if (substr in str[index] or substr == '*'):
                print(str[index])
        index += 1


def get_int_input(prompt_str, minn, maxx):
    while 1:
        try:
            n = int(raw_input(prompt_str))
            if not (minn <= n <= maxx):
                raise ValueError()
            else:
                break
        except ValueError:
            print("enter an integer between " +
                  str(minn) + ' and ' + str(maxx))
    return n


if __name__ == '__main__':
    """Show status of the Cluster Genesis environment

    Args:
        INV_FILE (string): Inventory file.
        LOG_LEVEL (string): Log level.

    Raises:
       Exception: If parameter count is invalid.
    """

    LOG = Logger(__file__)

    ARGV_MAX = 3
    argv_count = len(sys.argv)
    if argv_count > ARGV_MAX:
        try:
            raise Exception()
        except:
            LOG.error('Invalid argument count')
            sys.exit(1)

    INV_FILE = sys.argv[1]
    LOG.set_level(sys.argv[2])

    main(LOG, INV_FILE)
