#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import urllib3
from datetime import datetime
from datetime import timedelta
import logging
from orchestration_functions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

set_basic_logging()

"""
Creates a one-time patch deployment with a defined begin and end time. 
The json configuration is built using the user defined variables and then passed into the API call to generate the 
deployment in Tanium.
"""

##############################################################################################################
# Key Variables # Please update to your environment specifications #
##############################################################################################################

##############################################################################################################
# WARNING! # Be careful with inputs. Invalid inputs will break Tanium Patch module.
# If invalid inputs are shipped, please contact your TAM to escalate to a Patch SME for
# patch.db surgery and to remove the invalid deployment. ECF deployment config item will also need to be removed.
##############################################################################################################

# computers to be targeted for patching for inputting into deployment configuration
# comma separated
targetedComputerNames = "test1.server.local,test2.server.local"

# Deployment Name variable for inputting into deployment configuration
deployment_name = "API Create Windows One-Time Deployment Test"
deployment_description = "Deployment generated via Patch API"

# generate deployment start time based on current time
# note, always Zulu time/format
now = datetime.now()
startTime = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# generate deployment end time based on current time + 1 day
# note, always Zulu time/format
endTime_no_format = datetime.now() + timedelta(days=1)
endTime = endTime_no_format.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Limiting Group name to retrieve the ID of and then use in deployment configuration
management_rights_group_name = "All Windows"

# Content Set name to retrieve the ID of and then use in deployment configuration
contentSetName = "Patch Content Set"

# Patch List id - check Tanium Patch Workbench to find the id
patchListIdsWithLatestVersion = 2

# true or false # LOWER-CASE ONLY
downloadImmediately = "true"
overrideBlacklists = "false"
overrideMaintenanceWindows = "false"
restart = "true"
useTaniumClientTimeZone = "false"

# this only applicable if use_endpoint_timezone is set to false
issuerTimezone = "America/Los_Angeles"

# distribute over time in minutes, integer only
distributeOverTimeMinutes = 0

##############################################################################################################
# build deployment configuration json and create deployment #
##############################################################################################################

# retrieve content set id for inputting into deployment configuration
contentSetId = get_content_set_id_by_name(contentSetName)

# retrieve management rights group id for inputting into deployment configuration
targetLimitingGroupIds = get_management_rights_group_id_by_name(management_rights_group_name)

# build patch deployment json config
deployment_configuration = {
        "name": deployment_name,
        "description": deployment_description,
        "osType": "windows",
        "contentSetId": contentSetId,
        "type": "install",
        "patchTaniumUids": [

        ],
        "patchListIdsWithLatestVersion": [
                patchListIdsWithLatestVersion
        ],
        "patchListIdsWithPinnedVersion": [

        ],
        # "taniumGroupIds": null
        "targetedComputerNames": targetedComputerNames,
        "targetLimitingGroupIds": [
                targetLimitingGroupIds
        ],
        "startTime": startTime,
        "endTime": endTime,
        "useTaniumClientTimeZone": useTaniumClientTimeZone,
        "issuerTimezone": issuerTimezone,
        "distributeOverTimeMinutes": distributeOverTimeMinutes,
        "downloadImmediately": downloadImmediately,
        "overrideBlacklists": overrideBlacklists,
        "overrideMaintenanceWindows": overrideMaintenanceWindows,
        "restart": restart

}

logging.info("Created patch deployment json configuration.")

# create the patch deployment in tanium
create_patch_deployment(deployment_configuration)
