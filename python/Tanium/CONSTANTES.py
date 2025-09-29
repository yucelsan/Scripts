#------------------------------------------------------------------------------------------------------
# This script manage Tanium via its API
#
# Author: M. Msahazi, P. Legoux, S. AYSAN
#------------------------------------------------------------------------------------------------------

import json
import socket

# Return Codes
RC_JOB_OK = "Job OK"
RC_JOB_OK_NAE = "Job OK, Not all endpoints"

RC_JOB_KO = "Job KO"
RC_JOB_KO_PSU = "Job KO, Some endpoints patching status unknown" 
RC_JOB_KO_PKO = "Job KO, Patching error"

RC_TAN_ERR = "Tanium API Error"

RC_ARGS_KO = "Args KO"
RC_ARGS_KO_UMG = "Job KO, Unmanaged action"

JOB_STATUS_CODE = {
    RC_JOB_OK: {
        "returnCategory": 1,
        "code": 0,
        "msg": "OK",
    },
    RC_JOB_OK_NAE: {
        "returnCategory": 1,
        "code": 0,
        "msg": "OK, Not all endpoints online",
    },
    
    RC_TAN_ERR: {
        "returnCategory": 2,
        "code": 701,
        "msg": "KO: Tanium API error",
        "ErrorType": "TaniumApiError"
    },
    
    RC_JOB_KO_PSU: {
        "returnCategory": 2,
        "code": 911,
        "msg": "KO: Some endpoints patching status unknown",
        "ErrorType": "UnmanagedError"
    },
    
    RC_ARGS_KO: {
        "returnCategory": 3,
        "code": 801,
        "msg": "KO: Bad arguments", "ErrorType": "ArgError",
    },
    
    RC_ARGS_KO_UMG: {
        "returnCategory": 4,
        "code": 811,
        "msg": "KO: Unmanaged action",
        "ErrorType": "UnmanagedAction"
    },
    
    RC_JOB_KO: {
        "returnCategory": 5,
        "code": 901,
        "msg": "KO: Job in error",
        "ErrorType": "UnmanagedError"
    },
    
    RC_JOB_KO_PKO: {
        "returnCategory": 5,
        "code": 921,
        "msg": "KO: Patching error",
        "ErrorType": "UnmanagedError"
    },
    
}


# Types d'infrastructures et de server functions
with open('TaniumEnhancedTags.json') as f:
    tmp = json.load(f)
INFRASTRUCTURE_TYPES = tmp["INFRASTRUCTURE_TYPES"]
SERVER_FUNCTIONS = tmp["SERVER_FUNCTIONS"]
_sf_ServerList = {}


# OS utilisés
WINDOWS = "Windows"
LINUX = "Linux"

# Quadrigramme des VM Tanium
TANIUM_QUADRIGRAM = "TANI"

# Types d'environnement
ENV_TYPE_NON_PROD = "NonProd"
ENV_TYPE_PROD = "Prod"

# VM d'execution
CURRENT_VM_FQDN = socket.getfqdn()
