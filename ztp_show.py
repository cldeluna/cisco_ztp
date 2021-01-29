#!/usr/bin/python -tt
# Project: cisco_ztp
# Filename: ztp_show
# claudia
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "1/29/21"
__copyright__ = "Copyright (c) 2018 Claudia"
__license__ = "Python"

import argparse
import netmiko
import textfsm
import os


def text_fsm_parse(template_fn, data):



    # Run the text through the FSM.
    # The argument 'template' is a file handle and 'raw_text_data' is a
    # string with the content from the show_inventory.txt file
    template = open(template_fn)
    re_table = textfsm.TextFSM(template)
    fsm_results = re_table.ParseText(data)
    print("in text_fsm_parse function")
    print(type(fsm_results))
    print(len(fsm_results))


    return fsm_results, re_table


def ssh_ztp(dev, shcmd="show ip dhcp binding"):

    # Only needed when parsing from Netmiko directly
    os.environ["NET_TEXTFSM"] = "./ntc-templates/templates"

    # RAW Parsing with Python

    fsm_template = "cisco_ios_show_ip_dhcp_binding.textfsm"
    print(f"\n===============  Netmiko ONLY ===============")
    try:
        dev_conn = netmiko.ConnectHandler(**dev)
        dev_conn.enable()
        response = dev_conn.send_command(shcmd)
        print(f"\nResponse is of type {type(response)}\n")
        print(response)
        # because the response is a string we need to do some string manipulation
        # first we need to split the string into lines


        # resp = response.splitlines()
        #
        # with open('test.txt', 'w') as sample_file:
        #     sample_file.write(response)

        # now we should have a list in the variable resp over which we can iterate
        # print(f"\nSplit Response is of type {type(resp)}\n")
        # print(resp)
        # find_string = "NXOS: version"
        # # look
        # for line in resp:
        #     if find_string in line:
        #         print(f"******** FOUND LINE! ******\n{line}\n")

    except Exception as e:
        print(e)


def main():


    user = 'admin'
    pwd = 'eia!now'
    sec = 'eia!now'
    #
    dev = {
        'device_type': 'cisco_ios',
        'ip' : '192.168.1.1',
        'username' : user,
        'password' : pwd,
        'secret' : sec,
        'port' : '22'
    }


# Standard call to the main() function.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script Description",
                                     epilog="Usage: ' python ztp_show' ")

    #parser.add_argument('all', help='Execute all exercises in week 4 assignment')
    parser.add_argument('-a', '--all', help='Execute all exercises in week 4 assignment', action='store_true',
                        default=False)
    arguments = parser.parse_args()
    main()
