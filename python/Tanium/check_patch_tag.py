#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

import urllib3
import time
import logging
from orchestration_functions import *

def check_patch_tag(computers_to_patch: list[str], patch_orchestration_tag: str):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    set_basic_logging()

    """
    check_patch_tag.py can used to verify that the apply_patch_tag.py is applied and is also responsible for forcing
    endpoints to re-evaluate the existence of the custom tag and group membership so that patching activity can be
    initiated faster on the endpoint.
    """

    ##############################################################################################################
    # check for the patch tag #
    ##############################################################################################################
    # compile the matches/regex for the question
    regex_computer_list = build_regex_computer_list(computers_to_patch)

    # you ABSOLUTELY MUST ask this question WITH the maxAge=60 after applying the custom tag to your endpoints
    # ECF/CX on endpoints is responsible for evaluating group membership
    # ECF/CX still adheres to question cache and answers and the Custom Tags sensors have a default maxAge of 10 minutes
    # we need to use the maxAge to force re-evaluation of Custom Tags, so that when CX evaluates membership,
    # it sees that thee patch_orchestration tag is now on the endpoint
    # which will allow the patch process to begin patching activity when it next evaluates the patch deployment
    # the patch process on endpoints will evaluate deployments every 60 seconds
    # if you do not ask this question, endpoints will not being patching asap
    # and they will start sometime in the next 1 - 20 minutes randomly

    # build custom tags question and json
    custom_tags_question_text = "Get Custom Tags?maxAge=60 contains " + str(patch_orchestration_tag) + " from all machines with Computer Name matches " + regex_computer_list
    custom_tags_question_data = {
        "query_text" : custom_tags_question_text
    }

    # api post to create the custom tags question in the tanium console
    custom_tags_question_id = generate_tanium_question_and_id(custom_tags_question_data)

    # logging.info("Sleeping 30 seconds before retrieving question results for Custom Tags...")
    # time.sleep(30)

    # we don't necessarily need to grab the question response % and results.
    # it is technically enough to force the re-eval for group membership on CX/patch process deployments
    # we can parse the results for more validation on the tags though
