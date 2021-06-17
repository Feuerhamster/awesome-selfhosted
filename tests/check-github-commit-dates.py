#!/usr/bin/env python3

""" A script to find github repo links and last commit dates in a markdown file

Requirements:
 - python3 github module (sudo apt install python3-github on Debian)
 - A personal access token (https://github.com/settings/tokens)

Usage:
 - Run awesome_bot --allow-redirect -f README.md beforehand to detect any error(4xx, 5xx) that would
   cause the script to abort
 - Github API calls are limited to 5000 requests/hour https://developer.github.com/v3/#rate-limiting
 - Put the token in your environment variables:
   export GITHUB_TOKEN=18c45f8d8d556492d1d877998a5b311b368a76e4
 - The output is unsorted, just pipe it through 'sort' or paste it in your editor and sort from there
 - Put the script in your crontab or run it from time to time. It doesn't make sense to add this
   script to the CI job that runs every time something is pushed.
 - To detect no-commit related activity (repo metadata changes, wiki edits, ...), replace pushed_at
   with updated_at

"""

import sys
import time
import re
import os
import requests
from datetime import *

__author__ = "nodiscc"
__copyright__ = "Copyright 2019, nodiscc"
__credits__ = ["https://github.com/awesome-selfhosted/awesome-selfhosted"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "nodiscc"
__email__ = "nodiscc@gmail.com"
__status__ = "Production"

###############################################################################

access_token = os.environ['GITHUB_TOKEN']


headers = {"Authorization": "Bearer " + access_token}

def run_query(query, variables):
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

query = '''
    query($owner: String!, $name: String!)
        {
            repository(owner:$owner, name:$name) {
            pushedAt
        }
    }'''

""" find all URLs of the form https://github.com/owner/repo """
with open(sys.argv[1], 'r') as readme:
    print('Testing ' + sys.argv[1])
    data = readme.read()
    #project_urls = re.findall('https://github\.com/.*', data)
    project_urls = re.findall('https://github\.com/([a-zA-Z\d\-\._]{1,39}/[a-zA-Z\d\-\._]{1,39})(?=\)|/|#\s)', data)
    print('Checking ' + str(len(project_urls)) + ' github repos.')
urls = sorted(set(project_urls))


""" Uncomment this to debug the list of matched URLs """
# print(str(urls))
# print(len(urls))
# with open('links.txt', 'w') as filehandle:
#     for l in urls:
#         filehandle.write('%s\n' % l)

# exit(0)

list = []
i = 0
""" load project metadata, output last commit date and URL """
for url in urls:
    split = url.split("/")
    o = 'sapioit'
    p = "URL-Shortener"
    variables = {
        "owner": split[0],
        "name": split[1]
    }
    r = run_query(query, variables)
    if r["data"]["repository"] is None:
        list.append('[] | Repo Does not Exist | https://github.com/'+url)
        print('Repo Does not Exist | https://github.com/'+url)
        i += 1
    else:
        r_date = datetime.strptime(r["data"]["repository"]["pushedAt"], '%Y-%m-%dT%H:%M:%SZ').date()
        if r_date < (date.today() - timedelta(days = 365)):
            list.append([r_date, 'https://github.com/'+url])
            print(str(r_date)+' | https://github.com/'+url)
            i += 1

if i > 0:
    sorted_list = sorted(list, key=lambda x: x[0])
    with open('github_commit_dates.md', 'w') as filehandle:
        filehandle.write('%s\n' % '###There were %s repos last updated over 1 year ago.' % str(i))
        filehandle.write('%s\n' % '| Date | Github Repo |')
        filehandle.write('%s\n' % '|---|---|')
        for l in sorted_list:
            filehandle.write('| %s | %s |\n' % (str(l[0]), l[1]))
    sys.exit(0)
