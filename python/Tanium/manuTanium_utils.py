#------------------------------------------------------------------------------------------------------
# This script manage Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

from tanium_login import Login

from CONSTANTES import *
from tanium_enhanced_tags import SHARED_CONSTANTS as ET_SC


# Méthode de formatage du Json renvoyé par les diffentes méthodes fonctionnelles
def format_returned_json(lg: Login, status_code, shell_args = None, returned_values = None):
    
    returned_dict = {
        "Action": None,
        "SessionId": lg.get_session_id(),
        "Status": {
            "StatusCode": None,
            "StatusTextShort": None,
            "StatusTextLong": None,
        }
    }
    
    if JOB_STATUS_CODE[status_code]["returnCategory"] == 1:
        returned_dict["Action"] = shell_args["Action"]
        returned_dict["Status"]["StatusCode"] = JOB_STATUS_CODE[status_code]["code"]
        returned_dict["Status"]["StatusTextShort"] = status_code
        returned_dict["Status"]["StatusTextLong"] = JOB_STATUS_CODE[status_code]["msg"]
        
        returned_dict["ReturnedValues"] = returned_values
        
        return returned_dict

    elif JOB_STATUS_CODE[status_code]["returnCategory"] == 2:
        returned_dict["Action"] = shell_args["Action"]
        returned_dict["Status"]["StatusCode"] = JOB_STATUS_CODE[status_code]["code"]
        returned_dict["Status"]["StatusTextShort"] = status_code
        returned_dict["Status"]["StatusTextLong"] = JOB_STATUS_CODE[status_code]["msg"]
        returned_dict["Status"]["ScriptError"] = {
            "ErrorMsg": returned_values,
        }

        return returned_dict
    
    elif JOB_STATUS_CODE[status_code]["returnCategory"] == 3:
        if shell_args is None:
            return format_returned_json(lg, RC_JOB_KO)
        else:
            returned_dict["Status"]["StatusCode"] = JOB_STATUS_CODE[status_code]["code"]
            returned_dict["Status"]["StatusTextShort"] = status_code
            returned_dict["Status"]["StatusTextLong"] = JOB_STATUS_CODE[status_code]["msg"]
            returned_dict["Status"]["ScriptError"] = {
                "ErrorType": JOB_STATUS_CODE[status_code]["ErrorType"],
                JOB_STATUS_CODE[status_code]["ErrorType"]: {
                     "ErrorCode": shell_args.status,
                     "ErrorMsg": shell_args.ARGS_STATUS[shell_args.status],
                },
            }
            
            return returned_dict
    
    elif JOB_STATUS_CODE[status_code]["returnCategory"] == 4:
        if shell_args is None:
            return format_returned_json(lg, RC_JOB_KO)
        else:
            returned_dict["Status"]["StatusCode"] = JOB_STATUS_CODE[status_code]["code"]
            returned_dict["Status"]["StatusTextShort"] = status_code
            returned_dict["Status"]["StatusTextLong"] = JOB_STATUS_CODE[status_code]["msg"]
            returned_dict["Status"]["ScriptError"] = {
                "ErrorType": JOB_STATUS_CODE[status_code]["ErrorType"],
                JOB_STATUS_CODE[status_code]["ErrorType"]: {
                    JOB_STATUS_CODE[status_code]["ErrorType"]: {
                        "Action": shell_args["Action"],
                    },
                },
            }
            
            return returned_dict

    elif JOB_STATUS_CODE[status_code]["returnCategory"] == 5:
        returned_dict["Status"]["StatusCode"] = JOB_STATUS_CODE[status_code]["code"]
        returned_dict["Status"]["StatusTextShort"] = status_code
        returned_dict["Status"]["StatusTextLong"] = JOB_STATUS_CODE[status_code]["msg"]
        returned_dict["Status"]["ScriptError"] = {
            "ErrorType": JOB_STATUS_CODE[status_code]["ErrorType"],
            JOB_STATUS_CODE[status_code]["ErrorType"]: {},
        }
        
        return returned_dict
    
    else:
        return format_returned_json(lg, RC_JOB_KO)


# Méthode technique d'appel des différentes méthodes fonctionnelles
def do_actions(lg: Login, args):

    '''
        Lancement des actions en fonction du paramêtre reçu dans le json
    '''
    
    sc = ET_SC()

    method = args.SUPPORTED_ACTIONS[args.shell_args["Action"]]["localAction"]
    params = [args.shell_args[param] for param in args.SUPPORTED_ACTIONS[args.shell_args["Action"]]["actionParameters"]]
    
    return_code, returned_values = method(lg, *params)
    return (return_code, format_returned_json(lg, return_code, args.shell_args, returned_values))

