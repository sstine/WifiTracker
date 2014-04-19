from __future__ import print_function
import pprint
import mechanize, urllib, re, urlparse, optparse, timeit, json
from bs4 import BeautifulSoup

lat_list = []
lon_list = []
found_mac_list = []



def wigleLogin(browser, username, password):
	browser.open('http://wigle.net')
	reqData = urllib.urlencode({'credential_0': username, 'credential_1': password})
	browser.open('https://wigle.net/gps/gps/main/login', reqData)
	
def wigleLookup(browser, netid):

	params = {}
	params['netid'] = netid
	reqParams = urllib.urlencode(params)
	respURL = 'https://wigle.net/gps/gps/main/confirmlocquery/'
	resp = browser.open(respURL, reqParams).read()
	mapLat = ''
	mapLon = ''
	rLat = re.findall(r'maplat=.*\&', resp)
	if rLat:
		mapLat = rLat[0].split('&')[0].split('=')[1]
	rLon = re.findall(r'maplon=.*\&', resp)
	if rLon:
		mapLon = rLon[0].split('&')[0].split('=')[1]

	soup = BeautifulSoup(resp)
	td = soup.find_all('td')

	for node in soup.findAll(attrs={'class': 'launchinner'}):
		if("An Error has occurred:too many queries  Please go back and try again." in node.text):
			response = 1200
			return response

	if (mapLat.__len__() > 0) & (mapLon.__len__() > 0):
		found_mac_list.append(netid)
		lat_list.append(mapLat)
		lon_list.append(mapLon)

	return 1

def main():
	parser = optparse.OptionParser('[-] Usage: '+\
		'-u <Wigle.net Username> -p <Wigle.net Password> -m <MAC Address File>')
	parser.add_option('-u', dest='username', type='string', \
		help='Wigle.net username')
	parser.add_option('-p', dest='password', type='string', \
		help='Wigle.net password')
	parser.add_option('-i', dest='macFile', type='string', \
		help='mac address file with an address on each line')
	parser.add_option('-j', dest='jsonOutputFilePath', type='string', \
		help='File to save JSON output to')
	parser.add_option('-c', dest='coordsOutputFilePath', type='string', \
		help='File to save coordinates to')
	parser.add_option("-v",
                  action="store_true", dest="verbose", default=False,
                  help="Increase verbosity: print JSON output to the command line")

	(options, args) = parser.parse_args()
	if (options.username == None) | (options.password == None) | (options.macFile == None):
		print(parser.usage)
		exit(0)
	if (options.jsonOutputFilePath == None) & (options.coordsOutputFilePath == None) & (options.verbose == False):
		print("Specify either a JSON output file path, coordinates output file path, or increase verbosity.")
		exit(0)
	macFile = options.macFile
	jsonOutputFilePath = options.jsonOutputFilePath
	coordsOutputFilePath = options.coordsOutputFilePath
	verbose = options.verbose
	print('[+] Reading input from ' + macFile)

	f = open(macFile)
	records = [line.strip().split(',') for line in open(macFile)]
	f.close()

	macAddressesTotal = list([i[0] for i in records]) #list holds all mac addresses

	macAddresses = set(macAddressesTotal) #Grabs all unique mac addresses from the input
	times = list([i[1] for i in records]) #Puts all times in a list

	print("[+] Imported a total of " + str(len(macAddresses)) + " unique MAC Addresses "\
		"and " + str(len(times)) + " records")
	#exit(0)

	username = options.username
	password = options.password
	start = timeit.default_timer()
	browser = mechanize.Browser()
	wigleLogin(browser, username, password)
	print("[+] Logged into Wigle")

	count = 0
	for macAddress in macAddresses:
		print("[+] Querying MAC Address " + str(count))
		response = wigleLookup(browser, macAddress)
		if (response == 1):
			count = count + 1
		if(response == 1200):
			output = "{} {}: {}".format("[!] Error", response, "Too many requests")
			print(output)
			break

	if (len(lat_list) > 0) & (len(lon_list) > 0):

		print("[+] Found coordinates for " + str(len(lat_list)) + " Mac Addresses" )

		#Now we need to match the coordinates with their timestamps (1 to many relationship)
		#Start by finding which indices in the records list contain the mac addresses
		output = ""
		list_count = 0
		indices = []
		combined_times_array = []
		mac_times_dict = {}
		mac_times_array = []
		for foundMacAddress in found_mac_list:
			indices = [i for i, x in enumerate(macAddressesTotal) if x == foundMacAddress]
			output+= "['<b>" + foundMacAddress + "</b>"
			grouped_times = []
			#grouped_times = {}
			single_element = {}
			single_element["mac"] = foundMacAddress
			single_element["lat"] = lat_list[list_count]
			single_element["lon"] = lon_list[list_count]
			count = 0

			for index in indices:
				grouped_times.append(times[index])
				output+= "<br>" + times[index]
				count += 1
			single_element["times"] = grouped_times
			mac_times_array.append(single_element)
			
			output+= "',"
			output+= lat_list[list_count] + ","
			output+= lon_list[list_count] + "],"
			list_count += 1
		
		json_output = json.dumps(mac_times_array)
		if(verbose):
			print("[+] JSON Output: ")
			print(json_output)

		if(jsonOutputFilePath):
			output_file = open(jsonOutputFilePath, 'w')
			print(json_output, end="", file=output_file)
			print("[+] Saved JSON output to " + jsonOutputFilePath)

		if(coordsOutputFilePath):
			coords_output_file = open(coordsOutputFilePath, 'w')
			for lat, lon in zip(lat_list, lon_list):
				output = "{},{}".format(lat, lon)
				print(output, end="\n", file=coords_output_file)
			print("[+] Saved raw coordinates output to " + coordsOutputFilePath)
	else:
		print("[!] No coordinates found for the submitted mac addresses.")

	stop = timeit.default_timer()
	time_output = "{}: {}{}".format("Execution Time", stop-start, " seconds")
	print(time_output)
	

if __name__ == "__main__":
	main()