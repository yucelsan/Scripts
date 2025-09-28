#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import time
from datetime import datetime

from tanium.orchestration_functions import \
     generate_tanium_question_and_id, \
     get_question_result_info, \
     calculate_question_completion_percentage, \
     get_question_results_by_id
from tanium_login import Login

"""
get_patch_deployment_status.py can be used to retrieve the patch deployment status of a group of endpoints. 
Once the question is posted in Tanium, we wait a maximum of 60 seconds (modifiable) or until we reach 99% endpoint 
response before collecting the results and saving them into variables for processing.
"""

def verification_get_patch_deploy_status_script(lg: Login, deployment_id):
##############################################################################################################
# get patch deployment status #
##############################################################################################################

    lg.log_info("Beginning process to check the status of deployment: " + str(deployment_id))

    # build the deployment status question json
    deployment_status_question_text = ("Get Computer Name and Operating System and Last Reboot?maxAge=300 and Patch - Deployment Statuses matches \"^" +
                                      str(deployment_id) +
                                      "\|.*$\" from all machines with Patch - Deployment Statuses?maxAge=60 matches \"^" +
                                      str(deployment_id) +
                                      "\|.*$\"")
    deployment_status_question_data = {
        "query_text" : deployment_status_question_text
    }

    # post/create the deployment status question in tanium
    deployment_status_id = generate_tanium_question_and_id(lg, deployment_status_question_data)

    lg.log_info("Sleeping 30 seconds before retrieving patch deployment question results...")
    time.sleep(30)

    # grab the result info to feed into calculate_question_completion_percentage
    deployment_status_result_info = get_question_result_info(lg, deployment_status_id)

    # calculating the current question response %
    deployment_status_question_completion_percentage = calculate_question_completion_percentage(lg, deployment_status_result_info)

    # initializing and starting timeout for the while loop
    timeout = 60
    timeout_start = time.time()

    # NEEDS WORK - timer/timeout interval adjustments? what do we do if question completion % sucks?
    # while loop to check question completion percentage every 5 seconds; timeout after 60 seconds

    while (time.time() <= timeout_start + timeout and deployment_status_question_completion_percentage < 0.99):
        ctr += 1
        lg.log_info(f'5s sleep')
        time.sleep(5)

        deployment_status_result_info = get_question_result_info(lg, deployment_status_id)

        deployment_status_question_completion_percentage = calculate_question_completion_percentage(lg, deployment_status_result_info)

    # Retrieve question results themselves, not the question metadata
    patch_deployment_results = get_question_results_by_id(lg, deployment_status_id)

    # loop the result set for all rows and cache/write out the computer name and it's relevant deployment status
    row_counter = 0
    return_dict = {}
    while row_counter < patch_deployment_results['data']['result_sets'][0]['row_count']:
        computer_name = patch_deployment_results['data']['result_sets'][0]['rows'][row_counter]['data'][0][0]['text']
        operating_system = patch_deployment_results['data']['result_sets'][0]['rows'][row_counter]['data'][1][0]['text']
        last_reboot_time = patch_deployment_results['data']['result_sets'][0]['rows'][row_counter]['data'][2][0]['text']
        deployment_status = patch_deployment_results['data']['result_sets'][0]['rows'][row_counter]['data'][5][0]['text']
        lg.log_info(computer_name + " (" + operating_system + ")" + " has a last reboot time of: " + last_reboot_time + " and a patch deployment status of: " + deployment_status + ' - Last update time (queried from Tanium): ' + str(datetime.now()))
        return_dict[computer_name] = {"LastReboot": last_reboot_time, "DeploymentStatus": deployment_status}
        row_counter += 1

    return return_dict

    # note: there's not much in the way here of handling scenarios where we have 100% completion, but get no results back
    # no results would be an indicator that patching activity hasn't begun on the endpoint yet
    # that could be due to a missing patch_tag to make it a part of the targeted deployment
    # it could also be a missing deploy configuration file on the endpoint (ECF)
    # additionally, there are other scenarios where the TC might be broken/not responding or the deployment id variable
    # that's passed in isn't the correct deployment id to be checking for

    # depending on if we're using an ongoing deployment vs single deployment...
    # if this was a single deployment, this script would be fine as-is, once we validate the Complete status, we move on
    # if this was an ongoing deployment, we'll need more logic to handle and make sure all of the recently tagged
    # machines are all reporting a status, a simple if loop to validate that if a machine was sent for tagging -> that it
    # is also reporting a status/is responding to this question, if it's not responding after 10+ minutes,
    # we can wait a little longer or it may warrant throwing a log error that there's an issue with the endpoint
