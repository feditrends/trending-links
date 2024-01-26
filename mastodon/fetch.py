from datetime import datetime
import os
import time
from time import sleep
import json
import requests
from bs4 import BeautifulSoup
import sqlite3
import socket
import requests.packages.urllib3.util.connection as urllib3_cn

# Absolute path to current directory
path = os.path.dirname(__file__)

# Hack to for IPv4 for Requests, to avoid IPv6 timeout issues
def allowed_gai_family():
    family = socket.AF_INET    # force IPv4
    return family
 
urllib3_cn.allowed_gai_family = allowed_gai_family

# Setup DB connection
con = sqlite3.connect(os.path.join(path, "feditrends.db"))
con.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
cur = con.cursor()

# Function: Helper to remove any None values from dict (borrowed from: https://stackoverflow.com/a/44528129)
def clean_dict(raw_dict):
    return { k: ('' if v is None else v) for k, v in raw_dict.items() }
  
# Function: Extract Links
def extractLinks(instance, snapshot):

	links = []

	# Make the instance request
	try:

		# Construct URL
		links_url = "https://" + instance + "/api/v1/trends/links"

		for i in range(0, 5):

			# Set request parameters
			params = {
				'limit': 20,
				'offset': i * 20
			}

			new_links = requests.get(url = links_url, params = params, headers = {'Connection': 'close'}, timeout=10)

			links = links + new_links.json()

			# Sleep for 100ms so we're not bombarding the server
			sleep(0.1)

		# Loop through links
		for index, link in enumerate(links, start=1):

			linkMeta = {
				'link': link['url'],
				'rank': index,
				'uses_1d': int(link['history'][0]['uses']),
				'uses_total': sum(int(activity['uses']) for activity in link['history']),
				'instance': instance,
				'snapshot': snapshot
			}

			query = "INSERT INTO links " + str(tuple(linkMeta.keys())) + " values" + str(tuple(clean_dict(linkMeta).values())) + ";"
			cur.execute(query)
			con.commit()

	except requests.exceptions.RequestException as e:
			print("ERROR:", e)

# Snapshot timetamp
snapshot = int(time.time())

# Instance list
instances = ["mastodon.social", "mastodon.online", "hachyderm.io", "journa.host", "mstdn.social", "mas.to", "mastodon.world", "sfba.social", "c.im", "infosec.exchange", "sfba.social", "masto.ai", "techhub.social", "mastodon.sdf.org"]

print("SNAPSHOT START:", snapshot)

# Loop through instances
for instance in instances:
	print("INSTANCE START:", instance)
	extractLinks(instance, snapshot)
	print("INSTANCE COMPLETE:", instance)

print("SNAPSHOT COMPLETE:", snapshot)







