# Source:
# https://developer.cisco.com/docs/ios-xe/#!zero-touch-provisioning/ztp-with-http-server-running-on-ubuntu-vm
print "\n\n *** Sample ZTP Day0 Python Script *** \n\n"

# Importing cli module
import cli

print "\n\n *** Executing show version *** \n\n"
cli.executep('show version')

print "\n\n *** Configuring Management Interface *** \n\n"
# cli.configurep(["interface loop 100", "ip address 10.10.10.10 255.255.255.255", "end"])
cli.clip("configure terminal ; interface GigabitEthernet0/0 ; description MGMT_INT_BASE ; ip address dhcp ; no shutdown")

print "\n\n *** Executing show ip interface brief *** \n\n"
cli.executep('show ip int brief')

print "\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n"
