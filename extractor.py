from __future__ import print_function
from lxml import etree
import pprint, optparse, os

peerMacs = []
times = []

def clean(input_file, output_file):

	data = ""
	with open (input_file, "r") as input_file_handle:
		data=input_file_handle.read().replace('\n', '')
		data = data.replace('xmlns', 'name')
		
    	#print(data)

	with open(output_file, "w") as output_file_handle:
		output_file_handle.write(data)
		print("[+] Cleaned input file and saved to temporary file.")

def parseXML(input_file, output_file, cleaned_input_file):

	tree = etree.parse(cleaned_input_file)


	container = tree.getroot()
	count = 0

	connectionCount = 0
	errorLogCount = 0

	for event in container:
		record = "{}: {}".format("Connection", count)
		for elem in event:
			
			timeelem = elem.findall('TimeCreated')
			for time in timeelem:

				systemTime = time.get('SystemTime')
				times.append(systemTime)

			datalist = elem.findall('Data')
			for data in datalist:
				dataname = data.get('Name')
				if (dataname == 'PeerMac'):
					
					peerMac = data.text
					peerMacs.append(peerMac)
					connectionCount = connectionCount + 1
				if (dataname == 'FailureReason'):
					errorLogCount += 1
		count = count+1

		
		

		output_file_handle = open(output_file, 'w')
		for peerMac, time in zip(peerMacs, times):
			output = "{},{}".format(peerMac, time)
			print(output, end="\n", file=output_file_handle)

	print("[+] Parsed a total of " + str(count) + " logs.")
	
	ignoredCount = count - connectionCount
	print("[+] Ignored " + str(ignoredCount) + " logs that do not contain mac addresses.")
	print("[+] Saved data from " + str(connectionCount) + " valid connection logs to " + output_file)


def main():
	parser = optparse.OptionParser('[-] Usage: ' +\
		'-i <Input File> -o <Output File>')
	parser.add_option('-i', dest='input_file', type='string', \
		help='Exported Events Log in XML Format')
	parser.add_option('-o', dest='output_file', type='string', \
		help='Output file to save MAC addresses to')

	
	(options, args) = parser.parse_args()

	if(options.input_file == None) | (options.output_file == None):
		print(parser.usage)
		exit(0)

	input_file = options.input_file
	output_file = options.output_file


	print('[+] Parsing input from ' + input_file)
	clean(input_file, "temp.txt")
	parseXML(input_file, output_file, "temp.txt")
	os.remove("temp.txt")
	print("[+] Deleted temporary file.")


if __name__ == "__main__":
	main()
