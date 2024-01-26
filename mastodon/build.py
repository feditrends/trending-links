from datetime import datetime
import os
import json
import sqlite3
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from linkpreview import Link, LinkPreview, LinkGrabber
from liquid import Environment
from liquid import FileSystemLoader

# Absolute path to current directory
path = os.path.dirname(__file__)

# Setup DB connection
con = sqlite3.connect(os.path.join(path, "feditrends.db"))
con.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
cur = con.cursor()

# Set up the SQL query
sql = """
	SELECT
		link, 
		shares,
		row_number() over (order by score desc) as rank
	FROM 
		(SELECT
			link,
			count(distinct instance) as instances,
			max(uses_1d) as shares,
			(count(distinct instance) * max(uses_1d)) / max(rank) as score
		FROM links
		INNER JOIN (
			SELECT
				max(snapshot) as latest_snapshot
			FROM links
			) snapshots on links.snapshot = snapshots.latest_snapshot
		GROUP BY link
		HAVING instances > 5 AND score NOT NULL
		ORDER BY score DESC
		) ranking
"""

res = cur.execute(sql)
links = res.fetchall()

# Clean up old snapshots
maxsql = """
	SELECT max(snapshot) as maxsnap
	FROM links;
"""

maxget = cur.execute(maxsql)
maxsnap = maxget.fetchone()["maxsnap"]

cleansql = "DELETE FROM links WHERE snapshot != " + str(maxsnap) +  ";"

cur.execute(cleansql)
con.commit()
con.execute("VACUUM")

print("Old snapshots cleaned up")

# Hack to for IPv4 for Requests, to avoid IPv6 timeout issues
def allowed_gai_family():
    family = socket.AF_INET    # force IPv4
    return family
 
urllib3_cn.allowed_gai_family = allowed_gai_family

processed_links = []

for link in links:

	print("BEGIN:", link['link'])
	
	try:

		headers = {}

		# To avoid forced login
		if "twitter.com" in link['link']:
			headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

		# Look like a regular browser
		else:
			headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}

		grabber = LinkGrabber()
		content, url = grabber.get_content(link['link'], headers=headers)
		fetch_link = Link(url, content)
		preview = LinkPreview(fetch_link, parser="lxml")

		processed_link = {
			'url': link['link'],
			'title': preview.force_title,
			'description': preview.description,
			'image': preview.absolute_image,
			'share_count': link['shares'],
			'rank': link['rank'],
			'domain': preview.link.netloc.upper().replace("WWW.","")
		}

		if processed_link['title'] is not None:
			processed_links.append(processed_link)
			print("SUCCESS:", link['link'])

		else:
			print("ERROR [PREVIEW]:", link['link'])

	except:
		print("ERROR [LOAD]:", link['link'])

# Liquid template config
env = Environment(loader=FileSystemLoader(os.path.join(path, "templates/")))

# Load templates
json_template = env.get_template("trending-links.json")
rss_template = env.get_template("trending-links.xml")
html_template = env.get_template("trending-links.html")

# Render into templates
json_feed = json_template.render(links=processed_links)
rss_feed = rss_template.render(links=processed_links)
html_feed = html_template.render(links=processed_links)

# Write JSON Feed
json_file = open(os.path.join(path, "output/trending-links.json"), "w")
json_file.write(json_feed)
json_file.close()

# Write RSS
rss_file = open(os.path.join(path, "output/trending-links.xml"), "w")
rss_file.write(rss_feed)
rss_file.close()

# Write HTML
html_file = open(os.path.join(path, "output/trending-links.html"), "w")
html_file.write(html_feed)
html_file.close()