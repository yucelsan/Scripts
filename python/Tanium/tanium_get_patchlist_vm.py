#------------------------------------------------------------------------------------------------------
# This script get from VM to be patched from Tanium via its API
#
# Author: Tanium, P. Legoux, S. AYSAN, M. Msahazi
# 
#------------------------------------------------------------------------------------------------------
import time

from orchestration_functions import \
     generate_tanium_question_and_id, \
     get_question_result_info, \
     calculate_question_completion_percentage, \
     get_question_results_by_id, \
     get_patchlists
from tanium_login import Login

# Noms des OS utilisés
WINDOWS = "Windows"
LINUX = "Linux"

# Questions
backslash_b = "\\b"
PREDEFINED_QUESTIONS = {
    WINDOWS: {
        "VmToBePatched": 'Get Computer Name and Operating System and Patch - Patch List Applicability[0,1] matches "^[^|]*' +
                         backslash_b + \
                         '{P1}' + \
                         backslash_b + \
                         '[^|]*\|[^|]*\|[^|]*\|Not Installed\|.*$" from all machines with ( Is Windows equals True and ( Patch - Supported Scan Types matches ".*(Repo|Tanium|CAB|Online).*" and Patch - Supported Scan Types matches ".*(Repo|Tanium|CAB|Online).*" ) and Patch - Patch List Applicability[0,1] matches "^[^|]*' + \
                         backslash_b + \
                         '{P1}' + \
                         backslash_b + \
                         '[^|]*\|[^|]*\|[^|]*\|Not Installed\|.*$" )',
    },
    LINUX: {
        "VmToBePatched": 'Get Computer Name and Operating System and Patch - Patch List Applicability[0,1] matches "^[^|]*' + \
                         backslash_b + \
                         '{P1}' + \
                         backslash_b + \
                         '[^|]*\|[^|]*\|[^|]*\|Not Installed\|.*$" from all machines with ( All Computers and ( Patch - Supported Scan Types matches ".*(Repo|Tanium|CAB|Online).*" and Patch - Supported Scan Types matches ".*(Repo|Tanium|CAB|Online).*" ) and Patch - Patch List Applicability[0,1] matches "^[^|]*' + \
                         backslash_b + \
                         '{P1}' + \
                         backslash_b + \
                         '[^|]*\|[^|]*\|[^|]*\|Not Installed\|.*$" )',
    },
}


# Noms des Security Update Patch Lists Tanium
PATCH_LIST = {
    WINDOWS: "Windows CU",
    LINUX: "[Tanium Patch Baseline] - Linux",
}

def _return_endpoints(lg: Login, computer_name_question_text):
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

    lg.log_info(lg.LG_CHECK_COMPLETE_PATCH)
    lg.log_info("Endpoints to be patched are: " + str(endpoints_online))

    return endpoints_online


def _get_patchlist_id(lg: Login, patchlist_name):
    exit_status = True

    lg.log_info(f'Looking for patch list named "{patchlist_name}"')

    # return API response
    response = get_patchlists(lg)

    # Check if patchlist exists
    patchlists = response.get('patchLists')
    patchlist_names = {}
    for patchlist in patchlists:
        patchlist_names[patchlist.get('name')] = patchlist.get('id')

    # No such named patch list
    if patchlist_name not in patchlist_names.keys():
        lg.log_info(f'No patch list named "{patchlist_name}" found')
        
        exit_status = False
        return (exit_status, None)

    # Return patchlist ID
    pl_id = patchlist_names[patchlist_name]
    lg.log_info(f'Found patch list named "{patchlist_name}" with ID: {pl_id}')
    return (exit_status, pl_id)

def _get_vmlist(lg: Login, pl_id, os):
    exit_status = True

    lg.log_info(f'Looking for VM to be patched from patch list ID: {pl_id}')

    computer_name_question_text = PREDEFINED_QUESTIONS[os]["VmToBePatched"]
    computer_name_question_text = computer_name_question_text.replace("{P1}", str(pl_id))

    returned_endpoints = _return_endpoints(lg, computer_name_question_text)
    return (exit_status, [returned_endpoints]) if isinstance(returned_endpoints, str) else (exit_status, returned_endpoints)

def get_patchlist_vm(lg: Login, os):
    # Get patchlists
    lg.log_info(lg.LG_GET_PATCH)
    exit_status, pl_id = _get_patchlist_id(lg, PATCH_LIST[os])
    if not exit_status:
        return (exit_status, None, None)

    # Get VM list
    exit_status, vm_list = _get_vmlist(lg, pl_id, os)
    if not exit_status:
        return (exit_status, None, None)

    return (exit_status, vm_list, pl_id)


