#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

from datetime import datetime
from datetime import timedelta
from orchestration_functions import *
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# write to JSON file function
def write_json_file(data):
    outfile = open('./patchlist_response.json', 'w')
    outfile.write(json.dumps(data))
    outfile.close

# retrieve content set id
contentSetId = get_content_set_id_by_name("Patch Content Set")

# retrive patchlist id
patchlist_name = 'Test'
patchlist_names = []
response = get_patchlists()
patchlists = response.get('patchLists')
for patchlist in patchlists:
    if patchlist_name == patchlist.get('name'):
        patchlist_id = patchlist.get('id')

# retrieve computer group
group_name = 'Test'
response = get_computer_group(group_name)
group_id = response['data']['id']

# generate deployment start and end time
now = datetime.now()
start_time = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
end_time_no_format = datetime.now() + timedelta(days=1)
end_time = end_time_no_format.strftime("%Y-%m-%dT%H:%M:%S.000Z")

body = {
    "name": "Test Deployment",
    "description": "",
    "osType": "windows",
    "contentSetId": contentSetId,
    "type": "install",
    "downloadImmediately": True,
    "overrideBlacklists": True,
    "overrideMaintenanceWindows": True,
    "targetLimitingGroupIds": [],
    # "issuerTimezone": "Europe/London",
    "patchTaniumUids": [],
    "patchListIdsWithLatestVersion": [
        patchlist_id
    ],
    "patchListIdsWithPinnedVersion": [],
    "restart": False,
    "targetedComputerGroupIds": [
        group_id
    ],
    "targetedQuestionGroupIds": None,
    "targetedComputerNames": None,
    "useTaniumClientTimeZone": True,
    "startTime": start_time,
    "endTime": end_time,
    "distributeOverTimeMinutes": 120
}

response = create_patch_deployment(body)
write_json_file(response)
