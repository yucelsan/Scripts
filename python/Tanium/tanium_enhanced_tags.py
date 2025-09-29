#------------------------------------------------------------------------------------------------------
# This script get Enhanced tags from Tanium via its API
#
# Author: Tanium, M. Msahazi, P. Legoux, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import time

from orchestration_functions import generate_tanium_question_and_id, get_question_result_info, calculate_question_completion_percentage, get_question_results_by_id
from tanium_login import Login


class SHARED_CONSTANTS:

    APPLICATION_TAG = "ApplicationName"
    ENVIRONMENT_TAG ="EnvironmentType"
    INFRASTRUCTURE_TAG = "InfrastructureType"
    SERVER_FUNCTION_TAG = "ServerFunction"

    PROD_ENV = "Prod"
    NONPROD_ENV = "NonProd"

    _ENV_ERROR = "ENV ERROR"

    def revert_env(main, env):
        if env == main.PROD_ENV:
            return main.NONPROD_ENV
        elif env == main.NONPROD_ENV:
            return main.PROD_ENV
        else:
            return main._ENV_ERROR

sc = SHARED_CONSTANTS()

# Exemple provenant de la registry Computer\HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Tanium\Tanium Client\Sensor Data\EnhancedTags
# 
# Application
# P1 : hostnameapplicationnametags
# P2 : taniumapplicationname
# P3 : App-TANI
# Environment
# P1 : hostnameenvironmenttags
# P2 : taniumenvironmenttype
# P3 : Env-NonProd
# Location
# P1 : hostnamelocationtags
# P2 : taniumlocation
# P3 : Loc-MIA
# Server Function
# P1 : hostnameserverfunctiontags
# P2 : taniumserverfunction
# P3 : Sfunc-AS

PREDEFINED_QUESTIONS = {
    sc.ENVIRONMENT_TAG: {
        "P1": "hostnameenvironmenttags",
        "P2": "TaniumEnvironmentType", 
        "P3": {
                sc.PROD_ENV: "Env-Prod",
                sc.NONPROD_ENV: "Env-NonProd",
        },
        "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    },
    sc.APPLICATION_TAG: {
        "P1": "hostnameapplicationnametags",
        "P2": "TaniumApplicationName", 
        "P3": "App-",
        "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    },
    sc.INFRASTRUCTURE_TAG: {
        "P1": "hostnameinfrastructuretypetags",
        "P2": "TaniumInfrastructureType", 
        "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    },
    sc.SERVER_FUNCTION_TAG: {
        "P1": "hostnameserverfunctiontags",
        "P2": "TaniumServerFunction", 
        "Question": "Get Computer Name from all machines with Enhanced Tags - Single Value Exists[{P1},{P2},{P3}] equals True",
    },
}

##############################################################################################################
# Functions below # Please do not change #
##############################################################################################################

def _return_endpoints(lg, computer_name_question_text):
    computer_name_question_data = {"query_text" : computer_name_question_text}

    # api post to create the question in the tanium console
    computer_name_question_id = generate_tanium_question_and_id(lg, computer_name_question_data)

    lg.log_info(lg.LG_SLEEP_30)
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
    lg.log_info(lg.LG_GATHERING_RESULTS)
    computer_name_question_results = get_question_results_by_id(lg, computer_name_question_id)

    row_counter = 0
    endpoints_online = []
    lg.log_info(lg.LG_CHECKING_RESULTS)
    # loop all the rows returned

    while row_counter < computer_name_question_results['data']['result_sets'][0]['row_count']:
        # append the computer name to a list so we can track what's online as we loop the result set
        endpoints_online.append(computer_name_question_results['data']['result_sets'][0]['rows'][row_counter]['data'][0][0]['text'])
        row_counter += 1

    lg.log_info(lg.LG_CHECK_COMPLETE)
    lg.log_info("Online endpoints are: " + str(endpoints_online))

    return endpoints_online

def enhanced_tags_questions(lg: Login, tag_to_retreive, environment_type=None, quadrigram=None, server_function=None):
    exit_status = True
    if tag_to_retreive not in PREDEFINED_QUESTIONS.keys():
        exit_status = False
        return (exit_status, None)

    computer_name_question_text = PREDEFINED_QUESTIONS[tag_to_retreive]["Question"]
    computer_name_question_text = computer_name_question_text.replace("{P1}", PREDEFINED_QUESTIONS[tag_to_retreive]["P1"])
    computer_name_question_text = computer_name_question_text.replace("{P2}", PREDEFINED_QUESTIONS[tag_to_retreive]["P2"])

    if tag_to_retreive == sc.ENVIRONMENT_TAG:
        if environment_type is None or (environment_type != sc.PROD_ENV and environment_type != sc.NONPROD_ENV):
            exit_status = False
            return (exit_status, None)

        computer_name_question_text = computer_name_question_text.replace("{P3}", PREDEFINED_QUESTIONS[tag_to_retreive]["P3"][environment_type])

    elif tag_to_retreive == sc.APPLICATION_TAG:
        if quadrigram is None:
            exit_status = False
            return (exit_status, None)

        computer_name_question_text = computer_name_question_text.replace("{P3}", PREDEFINED_QUESTIONS[tag_to_retreive]["P3"] + quadrigram)

    elif tag_to_retreive == sc.SERVER_FUNCTION_TAG:
        if server_function is None:
            exit_status = False
            return (exit_status, None)

        computer_name_question_text = computer_name_question_text.replace("{P3}", server_function)
        
    else:
        exit_status = False
        return (exit_status, None)

    returned_endpoints = _return_endpoints(lg, computer_name_question_text)
    return (exit_status, [returned_endpoints]) if isinstance(returned_endpoints, str) else (exit_status, returned_endpoints)
