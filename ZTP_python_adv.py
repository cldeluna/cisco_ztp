import cli
import re
import json
import time

# source
# https://raw.githubusercontent.com/jeremycohoe/c9300-ztp/master/ztp-advanced.py

# Set Global variables to be used in later functions
tftp_server = '192.168.1.33'
# img_cat3k = 'cat3k_caa-universalk9.16.06.04.SPA.bin'
# img_cat3k_md5 = '41e56e88bb058ca08386763404b3ccb6'

img_cat9k = 'cat9k_iosxe.16.12.01.SPA.bin'
img_cat9k_md5 = '58755699355bb269be61e334ae436685'
software_version = 'Cisco IOS XE Software, Version 16.12.01'

img_cat9k = 'cat9k_iosxe.16.12.02.SPA.bin'
img_cat9k_md5 = '0d3e18f63f9ca52b6b056b27aa0d09e5'
software_version = 'Cisco IOS XE Software, Version 16.12.02'



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


def file_transfer(tftp_server, file, file_system='flash:/'):
    destination = file_system + file
    # Set commands to prepare for file transfer
    commands = ['file prompt quiet',
                'ip tftp blocksize 8192',
                'ip http client source-interface Gi0/0'
               ]
    results = cli.configurep(commands)
    print '*** Successfully set "file prompt quiet" and 8192 block size on switch ***'
    # transfer_file = "copy tftp://%s/%s %s vrf Mgmt-vrf" % (tftp_server, file, destination)
    # transfer_file = "copy http://%s/%s %s vrf Mgmt-vrf" % (tftp_server, file, file_system)
    transfer_file = "copy http://%s/%s %s" % (tftp_server, file, file_system)
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


def get_model():
    pass


def get_file_system():
    pass

def upgrade_required():
    # Obtains show version output
    sh_version = cli.cli('show version')
    # print("---->>>>> sh_version is \n" + sh_version)
    # Check if switch is on approved code: 16.10.01
    # JEREMY WAS HERE
    #match = re.search('%s', sh_version) (software_version)
    # JEREMY WAS HERE
    # Returns False if on approved version or True if upgrade is required
    if software_version in sh_version:
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
    print '###### STARTING ZTP INITIALIZATION SCRIPT ######'
    print '\n*** Obtaining serial number of device.. ***'
    serial = get_serial()
    print('*** Setting configuration file variable.. ***')
    config_file = "{}.cfg".format(serial)
    print('*** Config file: %s ***' % config_file)

    if upgrade_required():
        print '*** Upgrade is required. Starting upgrade process.. ***\n'
        if check_file_exists(img_cat9k):
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                print('*** Attempting to transfer image to switch.. ***')
                file_transfer(tftp_server, img_cat9k)
                if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                    raise ValueError('Failed Xfer')
        else:
            file_transfer(tftp_server, img_cat9k)
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                raise ValueError('XXX Failed Xfer XXX')

        # print '*** Deploying EEM upgrade script ***'
        # #install_activate_commit(img_cat9k)
        # deploy_eem_upgrade_script(img_cat9k)
        # print '*** Performing the upgrade - switch will reboot ***\n'
        # cli('event manager run upgrade')
        # time.sleep(600)
    else:
        print '*** No upgrade is required!!! ***'

    # Cleanup any leftover install files
    # print '*** Deploying Cleanup EEM Script ***'
    # deploy_eem_cleanup_script()
    # print '*** Running Cleanup EEM Script ***'
    # cli('event manager run cleanup')
    # time.sleep(30)

    if check_file_exists(config_file):
        print("===== Deleting Existing Staged Configuration File =====")
        del_cfg = "del flash:" + config_file
        cli.configurep(del_cfg)
        cli.configurep("\n")

    print("===== Transferring Configuration File =====")
    file_transfer(tftp_server, config_file)
    time.sleep(10)
    print '*** Removing any existing certs ***'
    find_certs()
    time.sleep(10)

    print '*** Deploying Base Configuration ***'
    hostname = "hostname SW_" + serial
    base_config = [
        hostname,
        "interface Gi0/0 ; no shutdown ; description MGMT ; ip address dhcp ; end",
        "aaa new-model",
        "aaa authentication login default local",
        "aaa authorization exec default local",
        "aaa session-id common",
        "username admin privilege 15 secret eia!now",
        "ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 192.168.1.1"
    ]
    try:
        domain_name = "uwaco.com"
        set_domain = "ip domain name " + domain_name
        cli.configurep(set_domain)
        cli.configurep('crypto key generate rsa modulus 2048')
        for cmd in base_config:
            cli.configurep(cmd)
        cli.clip("copy running-config startup-config")
    except Exception as e:
        print("ERROR! Could not apply base config.")
        print(e)

    print '###### FINISHED ZTP SCRIPT ######'


if __name__ in "__main__":
    main()