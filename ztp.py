import cli
import re
import json
import time
import argparse


def check_file_exists(file, file_system='flash:/'):
    dir_check = 'dir ' + file_system + file
    print '*** Checking to see if %s exists on %s ***' % (file, file_system)
    results = cli.cli(dir_check)
    if 'No such file or directory' in results:
        print '*** The %s does NOT exist on %s ***' % (file, file_system)
        return False
    elif 'Directory of %s%s' % (file_system, file) in results:
        print '*** The %s DOES exist on %s ***' % (file, file_system)
        return True
    else:
        raise ValueError("Unexpected output from check_file_exists")


def file_transfer(server, file, file_system='flash:/', protocol='http'):
    destination = file_system + file
    # Set commands to prepare for file transfer
    commands = ['file prompt quiet',
                'ip tftp blocksize 8192',
                'ip tftp source-interface Gi0/0',
                'ip http client source-interface Gi0/0'
               ]
    results = cli.configurep(commands)
    print '*** Successfully set "file prompt quiet" and 8192 block size on switch ***'
    # transfer_file = "copy tftp://%s/%s %s vrf Mgmt-vrf" % (server, file, destination)
    # transfer_file = "copy http://%s/%s %s vrf Mgmt-vrf" % (server, file, file_system)
    transfer_file = "copy %s://%s/%s %s" % (protocol, server, file, file_system)
    print("---->>>>> transfer_file is " + transfer_file)
    print 'Transferring %s to %s' % (file, file_system)
    transfer_results = cli.cli(transfer_file)
    if 'OK' in transfer_results:
        print '*** %s was transferred successfully!!! ***' % (file)
    elif 'XXX Error opening XXX' in transfer_results:
        raise ValueError("XXX Failed Xfer XXX")


def install_activate_commit(image):

    print '*** INSTALL ACTIVATE COMMIT (Silent) ***'

    install_command = 'install add file flash:' + image + ' activate commit prompt-level none'
    print("---->>>>> install_command is " + install_command)
    install_results = cli.cli(install_command)
    print('*** INSTALL Results ***')
    print(install_results)


def find_certs():
    certs = cli.cli('show run | include crypto pki')
    if certs:
        certs_split = certs.splitlines()
        certs_split.remove('')
        for cert in certs_split:
            command = 'no %s' % (cert)
            cli.configurep(command)

def get_serial():
    try:
        show_version = cli.cli('show version')
    except pnp._pnp.PnPSocketError:
        time.sleep(90)
        show_version = cli.cli('show version')
    try:
        serial = re.search(r"System Serial Number\s+:\s+(\S+)", show_version).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", show_version).group(1)
    return serial


def upgrade_required(sw_version):
    # Obtains show version output
    sh_version = cli.cli('show version')
    # print("---->>>>> sh_version is \n" + sh_version)
    print('\n====== Software Version Check %s ======' % sw_version)
    # Check if switch is on approved code: 16.10.01
    # JEREMY WAS HERE
    #match = re.search('%s', sh_version) (software_version)
    # JEREMY WAS HERE
    # Returns False if on approved version or True if upgrade is required
    if sw_version in sh_version:
        return False
    else:
        return True


def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
    verify_md5 = 'verify /md5 ' + file_system + image
    print 'Verifying MD5 for ' + file_system + image
    dst_md5 = cli.cli(verify_md5)
    if src_md5 in dst_md5:
        print '*** MD5 hashes match!! ***\n'
        return True
    else:
        print 'XXX MD5 hashes DO NOT match. XXX'
        return False


def main():
    # source
    # https://raw.githubusercontent.com/jeremycohoe/c9300-ztp/master/ztp-advanced.py

    # Set Global variables to be used in later functions
    http_server = '192.168.1.33'

    # img_cat9k = 'cat9k_iosxe.16.12.01.SPA.bin'
    # img_cat9k_md5 = '58755699355bb269be61e334ae436685'
    # software_version = 'Cisco IOS XE Software, Version 16.12.01'

    img_cat9k = 'cat9k_iosxe.16.12.04.SPA.bin'
    img_cat9k_md5 = '16e8583ca6184c54f9d9fccf4574fa6e'
    software_version = 'Cisco IOS XE Software, Version 16.12.04'

    print('====== STARTING ZTP INITIALIZATION SCRIPT ======')
    print('\n=== Obtaining serial number of device.. ===')
    serial = get_serial()
    print('\n\t--- ' + serial)
    print('--- Setting configuration file variable.. ---')
    config_file = "{}.cfg".format(serial)
    print('\n\t--- %s' % config_file)

    # Check to see if software upgrade is required:
    upgr_required = upgrade_required(software_version)
    if upgr_required:
        print('=== Upgrade is required. Starting Image File Transfer... ===\n')
        if check_file_exists(img_cat9k):
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                print('--- Attempting to transfer new image to switch after failed md5 check... ---')
                file_transfer(http_server, img_cat9k)
                if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                    raise ValueError('Failed Xfer')
        else:
            print('--- Attempting to transfer image to switch.. ---')
            file_transfer(http_server, img_cat9k)
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                raise ValueError('XXX Failed Xfer XXX')

    else:
        print('--- No upgrade is required!!! ---')

    if check_file_exists(config_file):
        print("===== Deleting Existing Staged Configuration File =====")
        del_cfg = "del /force flash:" + config_file
        cli.clip(del_cfg)

    print("===== Transferring Configuration File =====")
    file_transfer(http_server, config_file)
    time.sleep(10)
    print('--- Removing any existing certs ---')
    find_certs()
    time.sleep(10)

    print('--- Deploying Base Configuration ---')
    hostname = "hostname SW_" + serial
    base_config = [
        hostname,
        "interface GigabitEthernet0/0 ;description MGMT ;ip address dhcp ;no shutdown; end",
        "aaa new-model",
        "aaa authentication login default local",
        "aaa authorization exec default local",
        "aaa session-id common",
        "username admin privilege 15 secret eia!now",
        "ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 192.168.1.1"
    ]
    try:
        # domain_name = "uwaco.com"
        # set_domain = "ip domain name " + domain_name
        # cli.configurep(set_domain)
        # cli.configurep('crypto key generate rsa modulus 2048')
        for cmd in base_config:
            cli.configurep(cmd)
        cli.clip("configure terminal ; interface GigabitEthernet0/0 ; description MGMT_INT ; ip address dhcp ; no shutdown")
        cli.clip("copy running-config startup-config")
        # install_command = 'install add file flash:' + image + ' activate commit'
        # print("install command")
        # print(install_command)
        # cli.clip(install_command)
        # print("--->>> No don't save config")
        # cli.clip("n\n")
        # print("--->>> wait 600")
        # time.sleep(600)
        # print("--->>> Yes reboot")
        # cli.clip("y\n")
        # print("--->>> wait 600")
        # time.sleep(600)
        copy_cfg = "copy flash:" + config_file + " running-config"
        print("---->>>> Load config file {} into running configuration:".format(config_file))
        print("\t{}".format(copy_cfg))
        print(copy_cfg)
        result = cli.cli(copy_cfg)
        print("Load Result")
        print(result)
        domain_name = "net.cat.com"
        set_domain = "ip domain name " + domain_name
        print("===== Generating Crypto Key for domain %s =====".format(domain_name))
        cli.configurep(set_domain)
        cli.configurep('crypto key generate rsa modulus 2048')
    except Exception as e:
        print("ERROR! Could not apply base config.")
        print(e)

    print('###### FINISHED ZTP SCRIPT ######')


if __name__ in "__main__":
    main()