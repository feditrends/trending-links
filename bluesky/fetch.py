import sqlite3
import requests
import os

# Absolute path to current directory
path = os.path.dirname(__file__)

# Setup DB connection
con = sqlite3.connect(os.path.join(path, "skytrends.db"))
con.execute('pragma journal_mode=wal')
cur = con.cursor()

# Drop table if it exists
drop_sql = """
    DROP TABLE IF EXISTS links;
"""

# Create a fresh table
setup_sql = """
    CREATE TABLE IF NOT EXISTS links (
        link TEXT,
        reposts INTEGER,
        likes INTEGER
    );
"""

cur.execute(drop_sql)
cur.execute(setup_sql)
con.commit()
con.execute("VACUUM")

# Setup DB for easy insertion of dictionaries
con.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

# Function: Helper to remove any None values from dict (borrowed from: https://stackoverflow.com/a/44528129)
def clean_dict(raw_dict):
    return { k: ('' if v is None else v) for k, v in raw_dict.items() }
  
# Bluesky login credentials
BLUESKY_HANDLE = "example.bsky.social"
BLUESKY_APP_PASSWORD = "wwww-xxxx-yyyy-zzzz"

# Get JWT auth token
resp = requests.post(
    "https://bsky.social/xrpc/com.atproto.server.createSession",
    json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
)
resp.raise_for_status()
session = resp.json()
auth_token = session["accessJwt"]

# Function to extract URL from post
def getURL(post):

    # Start with empty variable
    url = None

    # Check if embed card exists at root level
    if 'embed' in post:
        try:
            url = post['embed']['external']['uri']
        except KeyError:
            url = None

    # Check if media embed card exists at root level
    if url is None:
        try:
            url = post['embed']['media']['external']['uri']
        except KeyError:
            url = None

    # Check if embed card exists at record level
    if url is None:
        try:
            url = post['record']['embed']['external']['uri']
        except KeyError:
            url = None

    # Check if link exists in facets
    if url is None:
        try:
            for facet in post['record']['facets']:
                if 'uri' in facet['features'][0]:
                    url = facet['features'][0]['uri']
        except KeyError:
            url = None

    # Follow URL shorteners
    shorteners = ['https://t.co', 'https://tinyurl.com', 'https://bit.ly']
    if url and any(x in url for x in shorteners):
        url = requests.get(url).url

    return url

# Global cursor
cursor = None

# Loop through 10 times (should get ~1000 posts at 100 per page)
for i in range(0, 20):

    # Log page being fetched
    print("Fetching page index: " + str(i))

    # Set up the request / did:plc:alyg3oh72qwze63x3nnpyhis/feed/aaaflp772pgye (this relies on Skyfeed, so this script won't work if that services goes down for some reason)
    getfeed_url = "https://bsky.social/xrpc/app.bsky.feed.getFeed"
    params = {
        'feed': 'at://did:plc:alyg3oh72qwze63x3nnpyhis/app.bsky.feed.generator/aaaflp772pgye',
        'limit': 100
    }

    # If cursor is set, add to params
    if cursor:
        params['cursor'] = cursor

    # Make the GET request
    feed = requests.get(url = getfeed_url, params = params, headers = {'Authorization': 'Bearer ' + auth_token, 'Connection': 'close'}, timeout=10)

    # Load posts into object
    posts = feed.json()['feed']

    # Iterate through posts and add to global object
    for post in posts:

        # Get counts
        try:
            details = {
                'reposts': int(post['post']['repostCount']),
                'likes': int(post['post']['likeCount'])
            }

        except KeyError:
            details = None

        # Get URL itself
        details['link'] = getURL(post['post'])

        # If URL determined, continue
        if details['link']:

            # Filtered domains (stuff that is more personal and less news-y / article-y)
            filtered = ['https://paypal.com', 'https://throne.com', 'https://instagram.com', "https://www.instagram.com", 'https://patreon.com', 'https://linktr.ee', 'https://twitter.com', 'https://x.com', 'https://ko-fi.com', 'https://fans.ly', 'https://etsy.com', 'https://paypal.me', 'https://bsky.app', 'https://gofund.me', 'https://allmylinks.com', 'https://dashare.zone', 'https://drive.google.com', "https://t.me", "https://fansly.com", "https://commons.wikimedia.org", "https://forms.gle"]
            
            if details['link'] and any(x in details['link'] for x in filtered):
                pass

            else:

                # Insert link into DB
                query = "INSERT INTO links " + str(tuple(details.keys())) + " values" + str(tuple(clean_dict(details).values())) + ";"
                cur.execute(query)
                con.commit()

    # Set the cursor
    try:
        cursor = feed.json()['cursor']
    
    # Or break
    except KeyError:
        print("Completed fetching")
        break