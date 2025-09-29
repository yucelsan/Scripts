#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------
from datetime import datetime, timedelta

from orchestration_functions import get_management_rights_group_id_by_name, create_patch_deployment
from tanium_login import Login

def patch_vm(lg: Login, VmType, FqdnList, PatchList_ID, EnvType, ApplicationQuadrigram):
    
    lg.log_info(lg.LG_DOING_PATCH)

    VMTYPE_LINUX = "Linux"
    VMTYPE_WINDOWS = "Windows"
    VMTYPES = [VMTYPE_LINUX, VMTYPE_WINDOWS]

    exit_status = True

    if VmType not in VMTYPES:
        exit_status = False
        return (exit_status, None)

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
    targetedComputerNames = ""
    for vm in FqdnList:
        targetedComputerNames += vm if targetedComputerNames == "" else f",{vm}"

    # Deployment Name variable for inputting into deployment configuration
    deployment_name = f"API Create {VmType} One-Time Deployment for {EnvType} {ApplicationQuadrigram} application"
    deployment_description = "Deployment generated via Patch API"

    # generate deployment start time based on current time
    # note, always Zulu time/format
    now = datetime.now()
    startTime = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # generate deployment end time based on current time + 2 hours
    # note, always Zulu time/format
    endTime_no_format = datetime.now() + timedelta(hours=2)
    endTime = endTime_no_format.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Limiting Group name to retrieve the ID of and then use in deployment configuration
    management_rights_group_name = 'Default - All computers'

    if VmType == VMTYPE_LINUX:
        # allSecurityUpdates or allUpdates
        updateType = "allSecurityUpdates"

    elif VmType == VMTYPE_WINDOWS:
        # Patch List id - check Tanium Patch Workbench to find the id
        patchListIdsWithLatestVersion = 2

    # true or false # LOWER-CASE ONLY
    downloadImmediately = "true"
    overrideBlacklists = "false"
    overrideMaintenanceWindows = "false"
    restart = "true"
    useTaniumClientTimeZone = "false"

    # this only applicable if use_endpoint_timezone is set to false
    issuerTimezone = "Europe/Paris"

    # distribute over time in minutes, integer only
    distributeOverTimeMinutes = 0

    ##############################################################################################################
    # build deployment configuration json and create deployment #
    ##############################################################################################################

    # retrieve content set id for inputting into deployment configuration
    contentSetId = PatchList_ID

    # retrieve management rights group id for inputting into deployment configuration
    #PLX targetLimitingGroupIds = get_management_rights_group_id_by_name(lg, management_rights_group_name)
    #PLX if targetLimitingGroupIds is None:
    #PLX    exit_status = False
    #PLX    return (exit_status, None)

    # build patch deployment json config
    if VmType == VMTYPE_LINUX:
        deployment_configuration = {
                "name": deployment_name,
                "description": deployment_description,
                "osType": VmType.lower(),
                "contentSetId": contentSetId,
                "type": "install",
                "osOptions": {
                        "updateType": updateType
                },
                # "patchTaniumUids": [
                #
                # ],
                # "patchListIdsWithLatestVersion": [
                #
                # ],
                # "patchListIdsWithPinnedVersion": [
                #
                # ],
                # "taniumGroupIds": null,
                "targetedComputerNames": targetedComputerNames,
                # PLX "targetLimitingGroupIds": targetLimitingGroupIds,
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

    elif VmType == VMTYPE_WINDOWS:
        deployment_configuration = {
                "name": deployment_name,
                "description": deployment_description,
                "osType": VmType.lower(),
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
                # PLX "targetLimitingGroupIds": [
                # PLX        targetLimitingGroupIds
                # PLX ],
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

    lg.log_info(f"Created patch deployment json configuration for {targetedComputerNames} ({VmType}).")

    # create the patch deployment in tanium
    patch_deployment_id = create_patch_deployment(lg, deployment_configuration)
    if patch_deployment_id is None:
        exit_status = False

    return (exit_status, patch_deployment_id)
