# Trending Links

This app will fetch trending links from a specified list of Mastodon instances, tempoarily write them to a SQLite database, and then produce HTML, RSS and JSON Feed outputs of the most poular links.

> [!NOTE]  
> This code is relatively hacky, but gets the job done. A few people have asked to see it out of curiosity, so it's presented here as-is.

## How to install & run

This has been tested on Python 3.11.7 but not extensively on other versions. Your mileage may vary. 

### 1. Install dependencies

`pip3 install -r requirements.txt`

### 2. Configure instance list

*(Optional)* Configure the instances you wish to fetch trending links from on Line 80 of `fetch.py`

### 3. Configure the database

Open up your terminal from the `/mastodon` directory, then run these commands to bootstrap your database.

Run sqlite3:

`sqlite3`

Load the database:

`.open feditrends.db`

Setup the table:

`.read setup.sql`

### 4. Fetch the links

`python3 fetch.py`

### 5. Build the outputs

`python3 build.py`

This will output the JSON Feed, RSS and HTML files to the `/output` directory. 

In a production environment, you should automate Steps 4 & 5 to run periodically with something like crontab, every 30 minutes or so. 

## The MIT License (MIT)
Copyright (c) 2024 feditrends

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
