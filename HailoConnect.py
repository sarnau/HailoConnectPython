#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii
import sys
import socket
import uuid
import time
import subprocess
import pprint

pp = pprint.PrettyPrinter()

# are we already connected to a Wifi network starting with 'LIB20_'?
# (This is macOS specific, please change for other operating systems)
process = subprocess.Popen(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport','-I'], stdout=subprocess.PIPE)
out, err = process.communicate()
process.wait()
wifi_info = {}
for line in out.decode("utf-8").split("\n"):
	if ": " in line:
		key, val = line.split(": ")
		key = key.replace(" ", "")
		val = val.strip()
		wifi_info[key] = val
if not wifi_info['SSID'].startswith('LIB20_'):
	# we are not connected to the correct Wifi network, so connect to it
	# with the password '0123456789'
	# (This is macOS specific, please change for other operating systems)
	import objc
	objc.loadBundle('CoreWLAN', bundle_path = '/System/Library/Frameworks/CoreWLAN.framework', module_globals = globals())
	iface = CWInterface.interface()
	networks, error = iface.scanForNetworksWithName_error_(None, None)
	found = False
	for network in networks:
		if network.ssid().startswith('LIB20_'):
			success, error = iface.associateToNetwork_password_error_(network, '0123456789', None)
			found = success != 0
			break
else:
	found = True

if not found:
	print("No connected to the Hallo Connect Wifi network")
	sys.exit(-1)

# The IP address of the device and the UDP port are fixed
UDP_IP = "192.168.10.11"
UDP_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', UDP_PORT))

gUUID = None
def getMacAddr():
	# generate a random MAC, ideally this would be persistent
	global gUUID
	if not gUUID:
		u = uuid.uuid4().bytes
		gUUID = (('%02x:' * 6) % (u[0] & 0xFE,u[1],u[2],u[3],u[4],u[5]))[:-1]
	return gUUID

def sendTo(hexStr):
	hexStr += getMacAddr().replace(':','')
	print("Send message: %s" % hexStr)
	sock.sendto(binascii.unhexlify(hexStr), (UDP_IP, UDP_PORT))
	time.sleep(0.250)
	data, addr = sock.recvfrom(14)
	print("Received message: %s" % binascii.hexlify(data))
	return binascii.hexlify(data)

def requestConfig():
	return sendTo('F1000000000000')
	# reply: Fx ledstatus, ledvalue, sensorstatus, sensorvalue, remotestatus, powervalue 6-BYTE-MAC

def requestStatistic():
	return sendTo('F2000000000000')
	# reply: Fx aa aa bb cc 0000 6-BYTE-MAC
	# aaaa and bbbb are unknown

def sendOpen():
	return sendTo('F7000000000000')

def sendConfig(sensorstatus, ledstatus, remotestatus, powervalue, ledvalue, sensorvalue):
	return sendTo(('F8' + '%02x' * 6) % (ledstatus, ledvalue, sensorstatus, sensorvalue, remotestatus, powervalue))


print(requestConfig())
