#------------------------------------------------------------------------------------------------------
# This script patch from VM from Tanium via its API
#
# Author: Tanium, P. Legoux, M. Msahazi, S. AYSAN
# 
#------------------------------------------------------------------------------------------------------

# Login : Initialisation et Logging 

import time
from datetime import datetime
import calendar
import configparser
import logging
import requests
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# login
class Login:

    LG_SLEEP_30 = "Sleeping 30 seconds before retrieving question results..."
    LG_GATHERING_RESULTS = "Gathering question results..."
    LG_CHECKING_RESULTS = "Checking question results for online endpoints communicating with Tanium..."
    LG_CHECK_COMPLETE = "Completed check for online endpoints."
    LG_CHECK_COMPLETE_PATCH = "Completed check for endpoints to be patched."
    LG_GET_PATCH = "Getting patchs lists"
    LG_DOING_PATCH = "Creating patch deployment in tanium"
    
    _LG_LOGIN = "-------------------- NEW SESSION STARTING --------------------"
    _LG_TESTING = "Testing Tanium URL and Token"
    _LG_LOGGED_IN = "Tanium URL and Token OK"

    RETURN_CODE_KO = "LG: Login KO"

    def __init__(self):
        
        config = configparser.ConfigParser()
        config.read('tanium_env_var.ini')

        self.tanium_server_url = config['environment']['tanium_server_url']
        self.api_token = config['environment']['api_token']
        self.log_location = config['logging']['log_location']

        current_GMT = time.gmtime()
        self.session_timestamp = calendar.timegm(current_GMT)

        self.set_basic_logging()
        self.log_info(self._LG_LOGIN)

        # Testing URL & Token
        self.log_info(self._LG_TESTING)
        action_group_url = self.tanium_server_url + "/api/v2/users"
        action_group_metadata = requests.get(action_group_url, headers={"session": self.api_token}, verify=False)
        if action_group_metadata.status_code != 200:
            self._login_msg = f"Tanium server don't allow connexions. Return code: {action_group_metadata.status_code}"
            self.login_status = False
            self.log_info(self._login_msg)
            return
        self.login_status = True
        self._login_msg = ""
        self.log_info(self._LG_LOGGED_IN)
        

    # used to init logging on other files to the single log location
    def set_basic_logging(self):
        logging.basicConfig(filename=self.log_location, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def log_info(self, info):
        logging.info(f'Session: {self.session_timestamp}, Msg: {info}')

    def get_session_id(self):
        return self.session_timestamp

    def get_login_status(self):
        return self._login_msg
