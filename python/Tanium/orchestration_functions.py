#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import requests
import urllib3
import time
from datetime import datetime
import json
import sys

from tanium_login import Login

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##############################################################################################################
# Functions below # Please do not change #
##############################################################################################################

# translates the package name to id; id is used in json configurations when creating actions w/ packages
def get_package_id_by_name(lg: Login, package_name):
    lg.log_info("Retrieving " + package_name + " package id...")
    package_url = lg.tanium_server_url + "/api/v2/packages/by-name/" + str(package_name)
    package_metadata = requests.get(package_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved package id: " + str(package_metadata.json()['data']['id']))
    return package_metadata.json()['data']['id']


# translates action group name to id; id is used in json configurations when creating actions
def get_action_group_id_by_name(lg: Login, action_group_name):
    lg.log_info("Retrieving " + action_group_name + " action group id...")
    action_group_url = lg.tanium_server_url + "/api/v2/action_groups/by-name/" + str(action_group_name)
    action_group_metadata = requests.get(action_group_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved action group id: " + str(action_group_metadata.json()['data']['id']))
    return action_group_metadata.json()['data']['id']


# translates the content set name to id
def get_content_set_id_by_name(lg: Login, content_set_name):
    lg.log_info("Retrieving " + content_set_name + " content set id...")
    content_set_url = lg.tanium_server_url + "/api/v2/content_sets/by-name/" + str(content_set_name)
    get_content_set_name = requests.get(content_set_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved content set id: " + str(get_content_set_name.json()['data']['id']))
    return get_content_set_name.json()['data']['id']


# translates the management rights group name to id
def get_management_rights_group_id_by_name(lg: Login, mr_name):
    lg.log_info("Retrieving " + mr_name + " management rights group id...")
    mr_url = lg.tanium_server_url + "/api/v2/management_rights_groups/by-name/" + str(mr_name)
    mr_metadata = requests.get(mr_url, headers={"session": lg.api_token}, verify=False)
    if mr_metadata.status_code != 200:
        lg.log_info("Orchestration function 'get_management_rights_group_id_by_name' returned error: " + str(mr_metadata.json()))
        return None
    lg.log_info("Retrieved management rights group id: " + str(mr_metadata.json()['data']['id']))
    return mr_metadata.json()['data']['id']


# combines computers names with a pipe | to use with matches/regex in the question
# NOTE currently no prevention mechanism built in to stop 100+ endpoint questions
# if computers_to_patched will exceed 100+ endpoints at a time,
# logic needs to be built to count, parse, and break it up into groups and loop this script through the different groups
def build_regex_computer_list(lg: Login, computers_to_add_to_list):
    lg.log_info("Building regex computer list...")
    number_of_computers_to_tag = len(computers_to_add_to_list)
    computer_count = 0
    while computer_count < number_of_computers_to_tag:
        if computer_count == 0:
            computer_list = computers_to_add_to_list[computer_count]
            computer_count += 1
        else:
            computer_list += "|" + computers_to_add_to_list[computer_count]
            computer_count += 1
    lg.log_info("Created regex computer list: " + computer_list)
    return computer_list


# uses the question data json to create the actual question in tanium; once posted, other functions can be used
# e.g. get_tanium_question_group_id can get the targeting portion of the question and the id can be used in an action
def generate_tanium_question_and_id(lg: Login, question_data):
    lg.log_info("Generating tanium question...")
    targeting_question_url = lg.tanium_server_url + "/api/v2/questions"
    tanium_question_metadata = requests.post(targeting_question_url, headers={"session": lg.api_token}, json=question_data, verify=False)
    lg.log_info("Created Question: " + question_data["query_text"])
    lg.log_info("Created Question ID: " + str(tanium_question_metadata.json()['data']['id']))
    return tanium_question_metadata.json()['data']['id']


# retrieves the group id (targeting portion) of a question; a question must be posted/created first
def get_tanium_question_group_id(lg: Login, tanium_question_id):
    lg.log_info("Retrieving Question Group ID for Question: " + str(tanium_question_id))
    question_url = lg.tanium_server_url + "/api/v2/questions/" + str(tanium_question_id)
    get_tanium_question_metadata = requests.get(question_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved Question Group ID: " + str(get_tanium_question_metadata.json()['data']['group']['id']))
    return get_tanium_question_metadata.json()['data']['group']['id']


# takes a json configuration (the package) as a parameter to create the action in tanium
def create_action_and_id(lg: Login, action_configuration):
    lg.log_info("Generating action...")
    create_action_url = lg.tanium_server_url + "/api/v2/actions"
    create_action_metadata = requests.post(create_action_url, headers={"session": lg.api_token}, json=action_configuration, verify=False)
    lg.log_info("Generated action with action id: " + str(create_action_metadata.json()['data']['id']))
    return create_action_metadata.json()['data']['id']


# create a patch deployment based on the json config parameter (patch_configuration) passed in
def create_patch_deployment(lg: Login, patch_configuration):
    lg.log_info("Creating patch deployment...")
    create_patch_deployment_url = lg.tanium_server_url + "/plugin/products/patch/v1/deployments"
    create_patch_deployment_metadata = requests.post(create_patch_deployment_url, headers={"session": lg.api_token},json=patch_configuration, verify=False)
    if create_patch_deployment_metadata.status_code != 200:
        lg.log_info("Orchestration function 'create_patch_deployment' returned error: " + str(create_patch_deployment_metadata.json()))
        return None
    lg.log_info("Created patch deployment id: " + str(create_patch_deployment_metadata.json()['id']))
    return create_patch_deployment_metadata.json()['id']

# stop a patch deployment based on id
def stop_patch_deployment(lg: Login, deployment_id):
    lg.log_info("Attempting to stop patch deployment: " + str(deployment_id))

    now = datetime.now()
    stopped_at = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    stop_configuration = {
        "stoppedAt": stopped_at
    }

    stop_patch_deployment_url = lg.tanium_server_url + "/plugin/products/patch/v1/deployments/" + str(deployment_id)
    stop_patch_deployment_metadata = requests.put(stop_patch_deployment_url, headers={"session": lg.api_token}, json=stop_configuration, verify=False)

    if stop_patch_deployment_metadata.status_code == 200:
        lg.log_info("Patch Deployment " + str(deployment_id) + " stopped successfully.")
    else:
        lg.log_info("Failed to successfully stop Patch Deployment " + str(deployment_id) + ". Please re-try or attempt to stop deployment via Tanium web console.")


# retrieves the responses and results in json format from an action id
def get_action_results(lg: Login, action_id):
    lg.log_info("Retrieving action status results...")
    action_results_by_id_url = lg.tanium_server_url + "/api/v2/result_data/action/" + str(action_id)
    get_action_results_metadata = requests.get(action_results_by_id_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved action results metadata in json format for action id: " + str(action_id))
    return get_action_results_metadata.json()


# parses the json from get_action_results to figure out how many endpoints responded to the action
def check_action_results_response_count(lg: Login, action_results_metadata, computers_targeted):
    lg.log_info("Checking endpoint response counts...")
    count_of_computers_responded = action_results_metadata['data']['result_sets'][0]['item_count']
    lg.log_info(str(count_of_computers_responded) + "/" + str(len(computers_targeted)) + " computers have responded to this action.")
    return count_of_computers_responded


# makes api get request to grab the question result info metadata in json format
# this result info json is then used in the calculate_question_completion_percentage function
# to figure out what percentage of endpoints of have responded which is then used
# to determine if we need to wait longer for more endpoints to respond/higher completion %
# or if we can proceed forward with grabbing the action question responses
def get_question_result_info(lg: Login, question_id):
    lg.log_info("Retrieving question results info from question id: " + str(question_id))
    question_result_info_url = lg.tanium_server_url + "/api/v2/result_info/question/" + str(question_id)
    question_result_info = requests.get(question_result_info_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved question results metadata in json format from question id: " + str(question_id))
    return question_result_info.json()


# calculate question completion percentage using some basic math and get_question_result_info
def calculate_question_completion_percentage(lg: Login, question_result_info):
    lg.log_info("Calculating question completion percentage...")
    tested_count_of_endpoints_responded = question_result_info['data']['result_infos'][0]['tested']
    estimated_total_count_of_endpoints_to_respond = question_result_info['data']['result_infos'][0]['estimated_total']
    question_completion_percentage = tested_count_of_endpoints_responded / estimated_total_count_of_endpoints_to_respond
    # need to fix the completion percentage printout
    lg.log_info("Calculated question completion percentage at: " + str(question_completion_percentage) + "%")
    return question_completion_percentage


# grabs the endpoint response metadata and returns it in json for parsing later with a separate function or other logic
def get_question_results_by_id(lg: Login, question_id):
    lg.log_info("Retrieving question results...")
    get_question_results_by_id_url = lg.tanium_server_url + "/api/v2/result_data/question/" + str(question_id)
    question_results_metadata = requests.get(get_question_results_by_id_url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrieved question results metadata in json format from question id: " + str(question_id))
    return question_results_metadata.json()


# get computer groups
def get_computer_group(lg: Login, group_name):
    lg.log_info("Fetching computer group...")
    url = lg.tanium_server_url + "/api/v2/groups/by-name/" + group_name
    response = requests.get(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Fetched computer groups")
    return response.json()

#############################################################################################################
# Patch List Functions
#############################################################################################################

# create a patch list based on the json config parameter (patchlist_configuration) passed in
def get_patchlists(lg: Login):
    lg.log_info("Fetching patch lists...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/patch-lists"
    response = requests.get(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Fetched patch lists")
    return response.json()

# create a patch list based on the json config parameter (patchlist_configuration) passed in
def create_patchlist(lg: Login, body):
    lg.log_info("Creating patch list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/patch-lists"
    response = requests.post(url, headers={"session": lg.api_token}, json=body, verify=False)
    lg.log_info("Created patch list ID " + str(response.json()['id']))
    return response.json()

# retrives a patch list using the patch ID
def get_patchlist(lg: Login, id):
    lg.log_info("Retriving patch list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/patch-lists/" + str(id)
    response = requests.get(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrived patch list ID " + str(id))
    return response.json()


# Updates a patch list using the patch ID
def update_patchlist(lg: Login, id, body):
    lg.log_info("Updating patch list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/patch-lists/" + str(id)
    response = requests.put(url, headers={"session": lg.api_token}, json=body, verify=False)
    lg.log_info("Updateded patch list ID " + str(id))
    return response.json()

# Deletes a patch list using the patch ID
def remove_patchlist(lg: Login, id):
    lg.log_info("Deleting patch list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/patch-lists/" + str(id)
    requests.delete(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Deleted patch list ID " + str(id))

#############################################################################################################
# Block List Functions
#############################################################################################################

# create a block list based on the json config parameter (patchlist_configuration) passed in
def create_blocklist(lg: Login, body):
    lg.log_info("Creating block list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/blacklists"
    response = requests.post(url, headers={"session": lg.api_token}, json=body, verify=False)
    lg.log_info("Created block list ID " + str(response.json()['id']))
    return response.json()

# retrives a block list using the patch ID
def get_blocklist(lg: Login, id):
    lg.log_info("Retriving block list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/blacklists/" + str(id)
    response = requests.get(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Retrived block list ID " + str(id))
    return response.json()


# Updates a block list using the patch ID
def update_blocklist(lg: Login, id, body):
    lg.log_info("Updating block list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/blacklists/" + str(id)
    response = requests.put(url, headers={"session": lg.api_token}, json=body, verify=False)
    lg.log_info("Updateded patch list ID " + str(id))
    return response.json()

# Deletes a block list using the patch ID
def remove_blocklist(lg: Login, id):
    lg.log_info("Deleting block list...")
    url = lg.tanium_server_url + "/plugin/products/patch/v1/blacklists/" + str(id)
    requests.delete(url, headers={"session": lg.api_token}, verify=False)
    lg.log_info("Deleted block list ID " + str(id))


#---------------------------------------------------------------------------------------------------------

