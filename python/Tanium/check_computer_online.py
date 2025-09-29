#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import urllib3
import time
import sys

from tanium_login import Login

from orchestration_functions import \
     build_regex_computer_list, \
     generate_tanium_question_and_id, \
     get_question_result_info, \
     calculate_question_completion_percentage, \
     get_question_results_by_id

"""
check_computer_online.py can be used to verify endpoints that are online and reporting in to Tanium. If an endpoint 
does not respond, either it is not online or there is an issue with the Tanium Client on that endpoint.

Note - there is also an alternate method to determine online and reporting to Tanium by using API calls to Client Status
"""

def verification_check_computer_script(lg: Login, computers_to_check):

    ##############################################################################################################
    # Key Variables # Please update to your environment specifications #
    ##############################################################################################################

    ##############################################################################################################
    # API call for generating the question #
    ##############################################################################################################
    # compile the matches/regex for the question
    regex_computer_list = build_regex_computer_list(lg, computers_to_check)
 
    # build question and json
    computer_name_question_text = "Get Computer Name from all machines with Computer Name matches " + regex_computer_list
    computer_name_question_data = {
        "query_text" : computer_name_question_text
    }

    # api post to create the question in the tanium console
    computer_name_question_id = generate_tanium_question_and_id(lg, computer_name_question_data)

    lg.log_info("Sleeping 30 seconds before retrieving question results...")
    time.sleep(30)

    # 30 seconds elapsed, grabbing the result info to pass into completion % check function
    computer_name_result_info = get_question_result_info(lg, computer_name_question_id)

    # calculate question response completion percentage
    computer_name_completion_percentage = calculate_question_completion_percentage(lg, computer_name_result_info)

    # 30 seconds have elapsed since asking the question
    # if at this point we are not at > 98% response,
    # then loop until we have exceeded 60 sec timeout or 98% of endpoints have responded
    question_timeout = 60
    timeout_timer = time.time()

    while time.time() <= timeout_timer + question_timeout and computer_name_completion_percentage < 0.98:
        lg.log_info('Question completion percentage has not reached 98% completion or the ' + str(question_timeout) + ' second timeout yet. Sleeping 5 seconds and checking again.')
        time.sleep(5)

        # grab the result info again for the question
        computer_name_result_info = get_question_result_info(lg, computer_name_question_id)

        # with new result info, calculate the current question completion response %
        computer_name_completion_percentage = calculate_question_completion_percentage(lg, computer_name_result_info)

    # with full endpoint responses to the question, we can now proceed with grabbing the actual question results
    lg.log_info("Gathering question results...")
    computer_name_question_results = get_question_results_by_id(lg, computer_name_question_id)

    row_counter = 0
    endpoints_online = []
    lg.log_info("Checking question results for online endpoints communicating with Tanium...")
    # loop all the rows returned

    while row_counter < computer_name_question_results['data']['result_sets'][0]['row_count']:
        # append the computer name to a list so we can track what's online as we loop the result set
        endpoints_online.append(computer_name_question_results['data']['result_sets'][0]['rows'][row_counter]['data'][0][0]['text'])
        row_counter += 1

    lg.log_info("Completed check for online endpoints.")
    lg.log_info("Online endpoints are: " + str(endpoints_online))
 
    return endpoints_online

