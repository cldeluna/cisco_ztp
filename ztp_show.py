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
import datetime
import netmiko
import textfsm
import shutil
import os
import re
import utils


def text_fsm_parse(template_fn, data):

    # Run the text through the FSM.
    # The argument 'template' is a file handle and 'raw_text_data' is a
    # string with the content from the show_inventory.txt file
    template = open(template_fn)
    re_table = textfsm.TextFSM(template)
    fsm_results = re_table.ParseText(data)
    # print("in text_fsm_parse function")
    # print(type(fsm_results))
    # print(len(fsm_results))

    return fsm_results



def get_show_cmd(dev, shcmd="show ip dhcp binding"):

    # RAW Parsing with Python
    response = ''
    try:
        dev_conn = netmiko.ConnectHandler(**dev)
        dev_conn.enable()
        response = dev_conn.send_command(shcmd)
        # print(f"\nResponse is of type {type(response)}\n")
        # print(response)
        # because the response is a string we need to do some string manipulation
        # first we need to split the string into lines

    except Exception as e:
        print("!Error - Netmiko connection to device failed!")
        print(e)

    return response


def ztp_dev_list(dev, shcmd="show ip dhcp binding"):

    # Only needed when parsing from Netmiko directly
    os.environ["NET_TEXTFSM"] = "./ntc-templates/templates"

    # RAW Parsing with Python

    fsm_template = "cisco_ios_show_ip_dhcp_binding.textfsm"
    print(f"\n===============  Netmiko SSH to {dev['ip']} ===============")
    try:
        dev_conn = netmiko.ConnectHandler(**dev)
        dev_conn.enable()
        response = dev_conn.send_command(shcmd)
        # print(f"\nResponse is of type {type(response)}\n")
        # print(response)
        # because the response is a string we need to do some string manipulation
        # first we need to split the string into lines

        # resp = response.splitlines()

        res = text_fsm_parse(fsm_template, response)
        # for ip in res:
        #     print(ip)

    except Exception as e:
        res = []
        print("!Error - Netmiko connection to device failed!")
        print(e)

    return res


def main():


    datestamp = datetime.date.today()
    print(f"===== Date is {datestamp} ====")

    # Seed the ZTP Hub Switch
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

    bindings_parsed = ztp_dev_list(dev)
    devs = []

    for line in bindings_parsed:
        # print(line)
        devs.append(line[0])

    if devs:
        print(f"The following IPs were found on the ZTP DHCP Server:")
        for d in devs:
            print(d)
    else:
        print(f"No staged devices were found!")
        exit("Aborting Run")

    fn = "show_cmds.yml"
    cmd_dict = utils.read_yaml(fn)

    # SAVING OUTPUT
    utils.sub_dir(arguments.output_subdir)

    for dev in devs:
        print(f"\n\n==== Device {dev}")
        devdict = utils.create_cat_devobj_from_json_list(dev)

        hn_cmd = ["show run | i hostname"]
        hn_response = utils.conn_and_get_output(devdict, hn_cmd)
        # print(hn_response)
        if len(hn_response) >= 7:
            hostname = hn_response.split(" ")[7].strip()
            print(f"\n---- Hostname {hostname}")
        else:
            hostname = dev

        if devdict['device_type'] in ['cisco_ios', 'cisco_nxos', 'cisco_wlc']:
            if arguments.show_cmd:
                cmds = []
                cmds.append(arguments.show_cmd)
            elif re.search('ios', devdict['device_type']):
                cmds = cmd_dict['staging_commands']
            elif re.search('nxos', devdict['device_type']):
                cmds = cmd_dict['nxos_show_commands']
            elif re.search('wlc', devdict['device_type']):
                cmds = cmd_dict['wlc_show_commands']
            else:
                cmds = cmd_dict['general_show_commands']
            resp = utils.conn_and_get_output(devdict, cmds, debug=True)
            # print(f"response is {resp}!")
            if resp:
                output_dir = os.path.join(os.getcwd(), arguments.output_subdir, f"{hostname}.txt")
                utils.write_txt(output_dir, resp)
            else:
                print(f"Device {dev} has no data!")



    ##  Zip the Dir
    # path to folder which needs to be zipped
    directory = f"./{arguments.output_subdir}"

    # calling function to get all file paths in the directory
    file_paths = utils.get_all_file_paths(directory)

    # writing files to a zipfile
    # Create zipfile name with timestamp

    # Optional Note to distinguish or annotate the show commands
    if arguments.note:
        note_text = utils.replace_space(arguments.note)
        zip_basefn = f"{arguments.output_subdir}_{datestamp}_{note_text}"
    else:
        zip_basefn = f"{arguments.output_subdir}_{datestamp}"

    if arguments.show_cmd:
        formatted_shcmd = utils.replace_space(arguments.show_cmd, debug=True)
        zip_fn = f"{zip_basefn}_{formatted_shcmd}"
    else:
        zip_fn = f"{zip_basefn}"

    if len(file_paths) > 0:
        # printing the list of all files to be zipped
        print('The following files will be zipped:')
        for file_name in file_paths:
            print(file_name)
        shutil.make_archive(zip_fn, 'zip', directory)
        print(f"All files zipped successfully to Zip file {zip_fn}!\n\n")
    else:
        print(f"No files with data to ZIP!")




# Standard call to the main() function.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script Description",
                                     epilog="Usage: ' python ztp_show' ")
    parser.add_argument('-o', '--output_subdir', help='Name of output subdirectory for show command files', action='store',
                        default="DEFAULT_STAGING_OUTPUT")
    parser.add_argument('-s', '--show_cmd', help='Execute a single show command across all devices', action='store')
    parser.add_argument('-n', '--note', action='store', help='Short note to distinguish show commands. Ex. -pre or -post')
    arguments = parser.parse_args()
    main()

