#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

from orchestration_functions import *
import urllib3
import pprint

# Ignore SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Write to JSON file
def write_json_file(data):
    outfile = open('./patchlist_response.json', 'w')
    outfile.write(json.dumps(data))
    outfile.close
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)

# Set Patch List ID
patchlist_id = str(9)

# Retrieve Patch List
response = get_patchlist(patchlist_id)

# Get rules from Patch List
rules = response.get('rules')

# Print Patch List
write_json_file(rules)
