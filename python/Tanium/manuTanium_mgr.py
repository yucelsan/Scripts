#------------------------------------------------------------------------------------------------------
# This script manage Tanium via its API
#
# Author: M. Msahazi, P. Legoux, S. AYSAN
#------------------------------------------------------------------------------------------------------

import sys
import json
import re

from tanium_login import Login
from manuTanium_utils import format_returned_json, do_actions

from CONSTANTES import *

import check_computer_online as chk_computer
from tanium_enhanced_tags import enhanced_tags_questions, SHARED_CONSTANTS as ET_SC
from tanium_get_patchlist_vm import get_patchlist_vm
from tanium_create_onetime_deployment import patch_vm
from tanium_get_patch_deployment_status import verification_get_patch_deploy_status_script


# Méthodes fonctionnelles permettant de faire réaliser les différentes actions à Tanium et générer les infos en retour
def do_GetVmList(lg, ApplicationQuadrigram, EnvironmentType, reverse=False):
    
    '''
        Obtention de la liste des VM pour un quadrigramme et un environement donné.
        La liste des VM retournées ne contient que celles dont le code SERVER_FUNCTIONS autorise leur patching
        automatique (ex: AS - Application Server - mais pas DC - Domain Controler).

        Un traitement spécifique est réalisé pour le cas des VM Tanium de production.
    '''


    sc = ET_SC()
    return_code = RC_JOB_OK

    return_list = []

    # récupération des VM d'un quadrigramme particulier
    exit_status, ApplicationQuadrigram_VmList = enhanced_tags_questions(lg, 
        sc.APPLICATION_TAG, quadrigram=ApplicationQuadrigram)
    if not exit_status:
        return_code = RC_TAN_ERR
        return (return_code, format_returned_json(lg, return_code))

    # recupération des VM d'un environnement particulier
    # NB: on peut utiliser SHARED_CONSTANTS.revert_env(EnvironmentType) pour avoir l'environnement inverse. Ex. SHARED_CONSTANTS.revert_env("Prod") -> "NonProd"
    env = sc.revert_env(EnvironmentType) if reverse else EnvironmentType
    exit_status, EnvironmentType_VmList = enhanced_tags_questions(lg, 
        sc.ENVIRONMENT_TAG, environment_type=env)
    if not exit_status:
        return_code = RC_TAN_ERR
        return (return_code, format_returned_json(lg, return_code))

    # croisement des deux listes et de la liste des SERVER_FUNCTIONS
    pattern = re.compile("^.{7}-.{4}(..)\d")
    for vm in ApplicationQuadrigram_VmList:
        if vm in EnvironmentType_VmList:
            match = pattern.match(vm)
            if match is None:
                continue

            function = match[1].upper()
            server_function_tag = "Sfunc-" + function
            if server_function_tag not in SERVER_FUNCTIONS:
                continue

            # Traitement du cas des VM Tanium de production
            if ApplicationQuadrigram == TANIUM_QUADRIGRAM and EnvironmentType == ENV_TYPE_PROD and vm == CURRENT_VM_FQDN:
                # une VM $U Tanium de production ne peut pas se patcher elle-même, on ne l'inclue pas dans la liste
                continue

            return_list.append(vm)

    # vérification si un patching est requis
    exit_status, windows_VmList, windows_PatchListId = get_patchlist_vm(lg, WINDOWS)
    if not exit_status:
        return_code = RC_TAN_ERR
        return (return_code, format_returned_json(lg, return_code))

    exit_status, linux_VmList, linux_PatchListId = get_patchlist_vm(lg, LINUX)
    if not exit_status:
        return_code = RC_TAN_ERR
        return (return_code, format_returned_json(lg, return_code))

    final_windows_return_list = []
    final_linux_return_list = []
    for vm in return_list:
        if vm in windows_VmList:
            final_windows_return_list.append(vm)
            continue
        if vm in linux_VmList:
            final_linux_return_list.append(vm)

    final_return_list = final_windows_return_list + final_linux_return_list

    # renvoi de la liste issue de ces croisements     
    return (
        return_code,
        {
            "VmList": {
                "FqdnList": {
                    WINDOWS: final_windows_return_list,
                    LINUX: final_linux_return_list,
                },
                "HostnameList": [vm.split(".", 1)[0] for vm in final_return_list],
            },
            "PatchListId": {
                WINDOWS: windows_PatchListId,
                LINUX: linux_PatchListId,
            },
        }
    )
    
def do_IsVmOnline(lg, FqdnList):

    '''
        Vérification de la visibilité par Tanium d'une liste de VM
        Retourne le statut de chacune
    '''
    
    # Exemple:
    #
    # json d'appel:
    #
    #    {
    #         "Action" : "IsVmOnline", 
    #         "VmList": [
    #             "test1.server.local", 
    #             "test2.server.local", 
    #             "Test3.server.local"
    #         ]
    #     }
    # json retourné:
    #
    #
##            check_status, status_endpoint = chk_computer.verification_check_computer_script(shell_args["VmList"])
##            if not check_status:
##                return_code = RC_TAN_ERR
##                return (return_code, format_returned_json(lg, return_code))

    sc = ET_SC()
    return_code = RC_JOB_OK

    VmList = FqdnList[WINDOWS] + FqdnList[LINUX]

    status_endpoint = chk_computer.verification_check_computer_script(lg, VmList)
        
    return_list = []
    online_list = []
    offline_list = []
    online_count = 0
    offline_count = 0
    for endpoint in VmList:
        if endpoint in status_endpoint:
            return_list.append({"VmName": endpoint, "Online": True})
            online_list.append(endpoint)
            online_count += 1
        else:
            return_list.append({"VmName": endpoint, "Online": False})
            offline_list.append(endpoint)
            offline_count += 1
            return_code = RC_JOB_OK_NAE

    return (
        return_code,
        {
            "VmListStatus": return_list, 
            "OnlineCount": online_count, 
            "OfflineCount": offline_count, 
            "OnlineVm": online_list, 
            "OfflineVm": offline_list
        }
    )

def do_GetVmTags(lg, FqdnList):

    '''
        Obtient de Tanium la liste des tags de chacune des VM de la liste
    '''
    
    # Exemple:
    #
    # json d'appel:
    #
    #    {
    #         "Action" : "GetVmTags", 
    #         "FqdnList": {
    #               "Windows": [
    #                   "test1.server.local",
    #               ],
    #               "Linux": [
    #                   "test2.server.local",
    #               ],
    #           },
    #     }
    # json retourné:
    #
    #

    sc = ET_SC()
    return_code = RC_JOB_OK

    return_list = []

    exit_status, nonprod_tagged_vm = enhanced_tags_questions(lg, 
        sc.ENVIRONMENT_TAG, environment_type=sc.NONPROD_ENV)
    if not exit_status:
        return_code = RC_TAN_ERR
        return (return_code, format_returned_json(lg, return_code))
    
    prod_tagged_vm = enhanced_tags_questions(lg, sc.ENVIRONMENT_TAG,
                                             environment_type=sc.PROD_ENV)

    return (
        return_code,
        {"NonProd_VmList": nonprod_tagged_vm, "Prod_VmList": prod_tagged_vm}
    )

def do_PatchVm(lg, FqdnList, PatchListId, EnvType, ApplicationQuadrigram):

    '''
        Fait réaliser à Tanium le patching de la liste de VM
    '''
    
    sc = ET_SC()
    return_code = RC_JOB_OK

    vm_by_os = {
        WINDOWS: {
            "VmList": FqdnList[WINDOWS],
            "PatchListId": PatchListId[WINDOWS],
            "patch_deployment_id": None,
            "patched_vm": None, # dict["patched_vm"] => {"LastReboot": last_reboot_time, "DeploymentStatus": deployment_status}
        },
        LINUX: {
            "VmList": FqdnList[LINUX],
            "PatchListId": PatchListId[LINUX],
            "patch_deployment_id": None,
            "patched_vm": None,
        },
    }


    # Soumission du patching
    for os in vm_by_os.keys():
        if len(vm_by_os[os]["VmList"]) != 0:
            return_code, vm_by_os[os]["patch_deployment_id"] = patch_vm(lg, os, vm_by_os[os]["VmList"], vm_by_os[os]["PatchListId"], EnvType, ApplicationQuadrigram)
            if not return_code:
                return_code = RC_JOB_KO_PKO
                return (return_code, format_returned_json(lg, return_code))


    # Boucle sur les id de déploiement pour obtenir l'avancement du patching
    for os in vm_by_os.keys():
        if len(vm_by_os[os]["VmList"]) != 0:
            vm_by_os[os]["patched_vm"] = verification_get_patch_deploy_status_script(lg, vm_by_os[os]["patch_deployment_id"])

    returned_VmList_Status = {"PatchingStatus": True, "PatchedVmStatus": {}}
    for os in vm_by_os.keys():
        for vm in vm_by_os[os]["VmList"]:
            if vm not in vm_by_os[os]["patched_vm"].keys():
                # pas obtenu de statut du patching de la VM
                returned_VmList_Status["PatchingStatus"] = False
                return_code = RC_JOB_KO_PSU
                returned_VmList_Status["PatchedVmStatus"][vm] = {}
            else:
                returned_VmList_Status["PatchedVmStatus"][vm] = {"Os": os, "PatchedVmStatus": vm_by_os[os]["patched_vm"][vm]}

    return (
        return_code,
        returned_VmList_Status
    )


def do_SetRemediationDateTag(lg, VmList):

    '''
        Positionne le tag de la date de patching réussi sur chacune des VM de la liste
    '''
    
    sc = ET_SC()
    return_code = RC_JOB_OK

    pass

def do_SetRemediationStatusTag(lg, VmList, Status, ApplicationQuadrigram, EnvironmentType, NonProdRemediationStatusTag=False):

    '''
        Positionne le tag du statut, réussi ou non, de patching sur chacune des VM de la liste.
        
        Dans le cas de VM d'environnement NonProd, il positionne aussi le tag sur les VM
        correspondantes de l'environnement de Prod afin de signaler que l'environnement de NonProd
        a été patché avec succès.
    '''
    
    sc = ET_SC()
    return_code = RC_JOB_OK

    # Application du tag RemediationStatusTag ou NonProdRemediationStatusTag à la valeur Status aux VM de VmList
    if NonProdRemediationStatusTag:
        pass # appeler le tagging NonProdRemediationStatusTag
    else:
        pass  # appeler le tagging RemediationStatusTag
        # Si environnement de NonProd
        if EnvironmentType == sc.NONPROD_ENV:
            exit_code, prod_list = do_GetVmList(lg, ApplicationQuadrigram,
                                                EnvironmentType,
                                                reverse=True)
            if exit_code == RC_JOB_OK:
                # Application du tag NonProdRemediationStatusTag aux VM de l'ApplicationQuadrigram correspondant en Prod
                exit_code, _ = do_SetRemediationStatusTag(lg, 
                    prod_list,
                    Status,
                    ApplicationQuadrigram,
                    sc.revert_env(EnvironmentType),
                    NonProdRemediationStatusTag=True)
    pass


# Classe technique d'obtention et de contrôle des Json fournis en paramêtre lors de l'appel du script
class Recup_args:

    # Codes retour de check du json en entrée
    RETURN_CODE_OK = 0
    RETURN_CODE_KO_NAO = 100
    RETURN_CODE_KO_NA  = 101
    RETURN_CODE_KO_NVA = 102
    RETURN_CODE_KO_NVL = 103
    RETURN_CODE_KO_MVA = 104
    RETURN_CODE_KO_NVS = 105
    RETURN_CODE_KO_NVJ = 106
    RETURN_CODE_KO_NPI = 107

    _VALID_STATUS_TAG = ["OK", "KO", "None"]

    _VALID_ENV_TYPE = [ENV_TYPE_PROD, ENV_TYPE_NON_PROD]
    
    ARGS_STATUS = {
        RETURN_CODE_OK: "OK",
        RETURN_CODE_KO_NAO: "ARGS: No args/option",
        RETURN_CODE_KO_NVJ: "ARGS: Not a valid json",
        RETURN_CODE_KO_NA: "ARGS: No action",
        RETURN_CODE_KO_NVA: "ARGS: No valid action",
        RETURN_CODE_KO_NVL: "ARGS: No VM list nor FQDN list",
        RETURN_CODE_KO_MVA: "ARGS: Missing valid action's arguments",
        RETURN_CODE_KO_NVS: "ARGS: No valid status",
        RETURN_CODE_KO_NPI: "ARGS: No patch list ID",
    }

    # Check de présence des arguments requis dans le json
    def _check_args_VmList_(self):
        return self.RETURN_CODE_KO_NVL if "VmList" not in self.shell_args.keys() or len(self.shell_args["VmList"]) == 0 else self.RETURN_CODE_OK

    def _check_args_FqdnList_(self):
        return self.RETURN_CODE_KO_NVL if "FqdnList" not in self.shell_args.keys() or len(self.shell_args["FqdnList"].keys()) == 0 else self.RETURN_CODE_OK

    def _check_args_ApplicationQuadrigram_(self):
        return self.RETURN_CODE_KO_MVA if "ApplicationQuadrigram" not in self.shell_args.keys() or len(self.shell_args["ApplicationQuadrigram"]) != 4 else self.RETURN_CODE_OK

    def _check_args_EnvironmentType_(self):
        return self.RETURN_CODE_KO_MVA if "EnvironmentType" not in self.shell_args.keys() or self.shell_args["EnvironmentType"] not in self._VALID_ENV_TYPE else self.RETURN_CODE_OK

    def _check_args_StatusTag_(self):
        return self.RETURN_CODE_KO_NVS if "StatusTag" not in self.shell_args.keys() or self.shell_args["StatusTag"] not in self._VALID_STATUS_TAG else self.RETURN_CODE_OK

    def _check_args_PatchList_ID_(self):
        return self.RETURN_CODE_KO_NPI if "PatchListId" not in self.shell_args.keys() or len(self.shell_args["PatchListId"]) == 0 else self.RETURN_CODE_OK


    # Définition des actions que peux appeler le json
    JSON_ACTION_GetVmList = "GetVmList"
    JSON_ACTION_IsVmOnline = "IsVmOnline"
    JSON_ACTION_GetVmTags = "GetVmTags"
    JSON_ACTION_PatchVm = "PatchVm"
    JSON_ACTION_SetRemediationDateTag = "SetRemediationDateTag"
    JSON_ACTION_SetRemediationStatusTag = "SetRemediationStatusTag"

    SUPPORTED_ACTIONS = {
        JSON_ACTION_GetVmList: {
            "check": [_check_args_ApplicationQuadrigram_, _check_args_EnvironmentType_], # Méthodes de vérification des éléments du json
            "localAction": do_GetVmList, # Méthode fonctionnelle
            "actionParameters": ["ApplicationQuadrigram", "EnvironmentType"], # Arguments du json passés à la méthode fonctionnelle
        },
        JSON_ACTION_IsVmOnline: {
            "check": [_check_args_FqdnList_],
            "localAction": do_IsVmOnline,
            "actionParameters": ["FqdnList"],
        },
        JSON_ACTION_GetVmTags: {
            "check": [_check_args_FqdnList_],
            "localAction": do_GetVmTags,
            "actionParameters": ["FqdnList"],
        },
        JSON_ACTION_PatchVm: {
            "check": [_check_args_FqdnList_, _check_args_ApplicationQuadrigram_, _check_args_EnvironmentType_, _check_args_PatchList_ID_],
            "localAction": do_PatchVm,
            "actionParameters": ["FqdnList", "PatchListId", "EnvironmentType", "ApplicationQuadrigram"],
        },
        JSON_ACTION_SetRemediationDateTag: {
            "check": [_check_args_VmList_],
            "localAction": do_SetRemediationDateTag,
            "actionParameters": [],
        },
        JSON_ACTION_SetRemediationStatusTag: {
            "check": [_check_args_VmList_, _check_args_StatusTag_],
            "localAction": do_SetRemediationStatusTag,
            "actionParameters": [],
        },
    }
    
    def __init__(self):
        self._read_shell_args() # Lecture des arguments fournis et du json
        self._check_args_()     # Vérification des fonctions et arguments

    def _read_shell_args(self):
        # Arguments fournis ?
        if len(sys.argv) == 1:
            self.shell_args = None
            self.status = self.RETURN_CODE_KO_NAO
            return
        
        # Lecture du json
        try:
            self.shell_args = json.loads(sys.argv[1])
            self.status = self.RETURN_CODE_OK
        except:
            self.shell_args = None
            self.status = self.RETURN_CODE_KO_NVJ
            return

    def _check_args_(self):
        # Action fournie ?
        if "Action" not in self.shell_args.keys():
            self.status = self.RETURN_CODE_KO_NA
            return
        
        if not self.shell_args["Action"] in self.SUPPORTED_ACTIONS.keys():
            self.status = self.RETURN_CODE_KO_NVA
        else:
            # Action et arguments ok ?
            for action in self.SUPPORTED_ACTIONS.keys():
                if self.shell_args["Action"] != action:
                    continue
                for check in self.SUPPORTED_ACTIONS[action]["check"]:
                    if self.status != self.RETURN_CODE_OK:
                        break
                    self.status = check(self)
                break


# Lancement du script
def main():
    lg = Login()
    args = Recup_args()

    if not lg.login_status:
        return_code = RC_TAN_ERR
        return_dict = format_returned_json(lg, return_code, returned_values=lg.get_login_status())
    elif args.status != args.RETURN_CODE_OK:
        return_code = RC_ARGS_KO
        return_dict = format_returned_json(lg, return_code, args)
    else:
        return_code, return_dict = do_actions(lg, args)

    print(json.dumps(return_dict))
    exit(JOB_STATUS_CODE[return_code]["code"])
    
    

if __name__ == "__main__":
    main()
