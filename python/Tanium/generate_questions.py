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
import logging
import json
import configparser
from orchestration_functions import *
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
set_basic_logging()


PREDEFINED_QUESTIONS = {
    "EnvironmentType": {
        "P1": "hostnameenvironmenttags",
        "P2": "EnvironmentType", 
        "P3": {
                "Prod": "Env-Prod",
                "NonProd": "Env-NonProd",
        },
        "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    },
    "ApplicationName": {

    },

    "InfrastructureType": {

    },

    "ServerFunction": {

    },

}

with open('EnhancedTags.json') as f:
    tmp = json.load(f)
INFRASTRUCTURE_TYPES = tmp["INFRASTRUCTURE_TYPES"]
SERVER_FUNCTION = tmp["SERVER_FUNCTION"]

##############################################################################################################
# init from tanium_env_var.ini # Please do not change #
##############################################################################################################

config = configparser.ConfigParser()
config.read('tanium_env_var.ini')

tanium_server_url = config['environment']['tanium_server_url']
api_token = config['environment']['api_token']
log_location = config['logging']['log_location']

##############################################################################################################
# Functions below # Please do not change #
##############################################################################################################


# used to init logging on other files to the single log location
def set_basic_logging():
    logging.basicConfig(filename=log_location, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


# build question and json
    # "EnvironmentType": {
    #     "P1": "hostnameenvironmenttags",
    #     "P2": "EnvironmentType", 
    #     "P3": {
    #             "Prod": "Env-Prod",
    #             "NonProd": "Env-NonProd",
    #     },
    #     "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    # },
computer_name_question_text = PREDEFINED_QUESTIONS["EnvironmentType"]["Question"]
computer_name_question_text = computer_name_question_text.replace("{P1}", PREDEFINED_QUESTIONS["EnvironmentType"]["P1"])
computer_name_question_text = computer_name_question_text.replace("{P2}", PREDEFINED_QUESTIONS["EnvironmentType"]["P2"])
computer_name_question_text = computer_name_question_text.replace("{P3}", PREDEFINED_QUESTIONS["EnvironmentType"]["P3"]["NonProd"])
computer_name_question_data = {
    "query_text" : computer_name_question_text
}

# api post to create the question in the tanium console
computer_name_question_id = generate_tanium_question_and_id(computer_name_question_data)

logging.info("Sleeping 30 seconds before retrieving question results...")
time.sleep(30)

# 30 seconds elapsed, grabbing the result info to pass into completion % check function
computer_name_result_info = get_question_result_info(computer_name_question_id)

# calculate question response completion percentage
computer_name_completion_percentage = calculate_question_completion_percentage(computer_name_result_info)

# 30 seconds have elapsed since asking the question
# if at this point we are not at > 98% response,
# then loop until we have exceeded 60 sec timeout or 98% of endpoints have responded
question_timeout = 60
timeout_timer = time.time()

while time.time() <= timeout_timer + question_timeout and computer_name_completion_percentage < 0.98:
    logging.info('Question completion percentage has not reached 98% completion or the ' + str(question_timeout) + ' second timeout yet. Sleeping 5 seconds and checking again.')
    time.sleep(5)

    # grab the result info again for the question
    computer_name_result_info = get_question_result_info(computer_name_question_id)

    # with new result info, calculate the current question completion response %
    computer_name_completion_percentage = calculate_question_completion_percentage(computer_name_result_info)

# with full endpoint responses to the question, we can now proceed with grabbing the actual question results
logging.info("Gathering question results...")
computer_name_question_results = get_question_results_by_id(computer_name_question_id)

row_counter = 0
endpoints_online = []
logging.info("Checking question results for online endpoints communicating with Tanium...")
# loop all the rows returned

while row_counter < computer_name_question_results['data']['result_sets'][0]['row_count']:
    # append the computer name to a list so we can track what's online as we loop the result set
    endpoints_online.append(computer_name_question_results['data']['result_sets'][0]['rows'][row_counter]['data'][0][0]['text'])
    row_counter += 1

logging.info("Completed check for online endpoints.")
logging.info("Online endpoints are: " + str(endpoints_online))


print(endpoints_online)