#!/bin/bash
# - PostInstall remove & uninstall agents 
# - Author : Serdar AYSAN
# - Company : YUCELSAN

PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:/usr/sfw/bin:$PATH
OS_BINARY_TYPE=''
OS_NAME=`uname -s`
OS_ARCH=`uname -m`
SUCCESS=0
WARNING=1
FAILURE=2
BOOL_TRUE='True'
BOOL_FALSE='False'
SUDO=''
CHANNEL='prod'
#CHANNEL='insiders-fast'
DISTRO=
DISTRO_FAMILY=
INSTALL_MODE=
VERSION=
VERBOSE=
PASSIVE_MODE=
ONBOARDING_SCRIPT=
OFFBOARDING_SCRIPT=
PRODUCT_NAME='POST_INSTALL_LINUX'
AGENT_NONROOT='0'
IS_VENV_SUPPORT_NEEDED=$BOOL_FALSE
ECHO_PRINT=5
THIRTY_TWO_BIT='32-bit'
SIXTY_FOUR_BIT='64-bit'
#LOCAL_SETUP=$BOOL_TRUE
LOCAL_SETUP=$BOOL_FALSE

#local
LOCAL_SERVER=''

# Error codes
ERR_INTERNAL=1
ERR_INVALID_ARGUMENTS=2
ERR_INSUFFICIENT_PRIVILAGES=3
ERR_NO_INTERNET_CONNECTIVITY=4
ERR_CONFLICTING_APPS=5
ERR_UNSUPPORTED_DISTRO=10
ERR_UNSUPPORTED_VERSION=11
ERR_INSUFFICIENT_REQUIREMENTS=12
ERR_CORRUPT_MDE_INSTALLED=15
ERR_MDE_NOT_INSTALLED=20
ERR_INSTALLATION_FAILED=21
ERR_UNINSTALLATION_FAILED=22
ERR_FAILED_DEPENDENCY=23
ERR_FAILED_REPO_SETUP=24
ERR_INVALID_CHANNEL=25
ERR_FAILED_REPO_CLEANUP=26
ERR_ONBOARDING_NOT_FOUND=30
ERR_ONBOARDING_FAILED=31
ERR_OFFBOARDING_NOT_FOUND=32
ERR_OFFBOARDING_FAILED=33
ERR_TAG_NOT_SUPPORTED=40
ERR_PARAMETER_SET_FAILED=41
ERR_UNSUPPORTED_ARCH=45

_log() {
    level="$1"
    dest="$2"
    msg="${@:3}"
    ts=$(date -u +"%Y-%m-%dT%H:%M:%S")

    if [ "$dest" = "stdout" ]; then
       echo "$msg"
    elif [ "$dest" = "stderr" ]; then
       >&2 echo "$msg"
    fi

    if [ -n "$log_path" ]; then
       echo "$ts $level $msg" >> "$log_path"
    fi
}

log_debug() {
    _log "DEBUG" "stdout" "$@"
}

log_info() {
    _log "INFO " "stdout" "$@"
}

log_warning() {
    _log "WARN " "stderr" "$@"
}

log_error() {
    _log "ERROR" "stderr" "$@"
}

print_green() {
    printf "\033[32m%s\033[0m\n" "$*"
}

print_console() {
    printf "%s\n" "$*"
}

print_red() {
    printf "\033[31m%s\033[0m\n" "$*"
}

print_done() {
    print_green "Done."
}

log() {
	if [ "$1" = "$ECHO_PRINT" ]; then
		echo "$2"
	fi
}	

detectArchitectureType(){
	if [[ "$OS_ARCH" = *"arm"* ]] || [[ "$OS_ARCH" = *"ARM"* ]] || [[ "$OS_ARCH" = *"Arm"* ]] || [[ "$OS_ARCH" = *"aarch"* ]] || [[ "$OS_ARCH" = *"ppc64le"* ]] || [[ "$OS_ARCH" = *"s390x"* ]] ; then
	  IS_VENV_SUPPORT_NEEDED=$BOOL_TRUE
	fi
	print_green "Detected OS ARCH : $OS_ARCH"
}

detectOs(){
	if [ "$OS_NAME" != "Linux" ]; then
		IS_VENV_SUPPORT_NEEDED=$BOOL_TRUE
	fi
	print_green "Detected OS : $OS_NAME"
}

detectSystemInfo() {
    # Détecte le nom du système
    if [ -f /etc/os-release ]; then
	source /etc/os-release
	if [ -n "$PRETTY_NAME" ]; then
	    print_green "Nom du système : $PRETTY_NAME"
	fi
    fi

    # Détecte la version du système
    if [ -f /etc/lsb-release ]; then
	source /etc/lsb-release
	if [ -n "$DISTRIB_DESCRIPTION" ]; then
	    print_green "Version du système : $DISTRIB_DESCRIPTION"
	fi
    elif [ -f /etc/debian_version ]; then
	debian_version=$(cat /etc/debian_version)
	print_green "Version du système : Debian $debian_version"
    elif [ -f /etc/redhat_release ]; then
	redhat_version=$(cat /etc/redhat_release)
	print_green "Version du système : $redhat_version"
    fi
}

checkShellUtility(){
	if command -v bash >/dev/null; then
		SHELL_UTILITY="bash"
	else
		SHELL_UTILITY="sh"
	fi
}

isRootUser() {
	if [ "$(id -u)" != "0" ]; then
		print_red "Please use 'sudo' or log in as root to execute the script"
		exit $FAILURE
	fi
}

isNonRootUser() {
	if [ "$(id -u)" == "0" ]; then
		print_red "Can't use -nonroot or -nr option when logged in as root"
		exit $FAILURE
	fi
}

checkForBinSupport(){
	checkShellUtility
	detectOs
	detectArchitectureType 2>/dev/null
	detectSystemInfo
}

deleteDirPostInstall() {
    print_red "*****   SUPRESSION DIRECTORY POST INSTALL  ***********"
    /usr/bin/sudo rm -rf /opt/script_postinstall
    printf "\n"
}

desinstallationAgentTanium() {
    print_red "*****************   TANIUM   *****************************"
    print_green "Désinstallation de l'agent Tanium en cours..."
    print_green "Detection de l'OS pour la suppression de Tanium..."
    # Détecte la version du système pour desinstaller Tanium
    if [ -f /etc/os-release ] || [ -f /etc/mariner-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
        VERSION_NAME=$VERSION_CODENAME
    elif [ -f /etc/redhat-release ]; then
        if [ -f /etc/oracle-release ]; then
            DISTRO="ol"
        elif [[ $(grep -o -i "Red\ Hat" /etc/redhat-release) ]]; then
            DISTRO="rhel"
        elif [[ $(grep -o -i "Centos" /etc/redhat-release) ]]; then
            DISTRO="centos"
        fi
        VERSION=$(grep -o "release .*" /etc/redhat-release | cut -d ' ' -f2)
    else
        print_red "unable to detect distro" $ERR_UNSUPPORTED_DISTRO
    fi

    # change distro to ubuntu for linux mint support
    if [ "$DISTRO" == "linuxmint" ]; then
        DISTRO="ubuntu"
    fi

    if [ "$DISTRO" == "debian" ] || [ "$DISTRO" == "ubuntu" ]; then
        DISTRO_FAMILY="debian"
	print_green "$DISTRO_FAMILY"
	/usr/bin/sudo dpkg -P taniumclient
    elif [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "ol" ] || [ "$DISTRO" == "fedora" ] || [ "$DISTRO" == "amzn" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
        DISTRO_FAMILY="fedora"
	print_green "$DISTRO"
	/usr/bin/sudo rpm -e $(rpm -qa --queryformat "%{NAME}\n" | grep -e '[Tt]anium[Cc]lient')
	/usr/bin/sudo rm -rf /opt/Tanium
    elif [ "$DISTRO" == "mariner" ]; then
        DISTRO_FAMILY="mariner"
    elif [ "$DISTRO" == "sles" ] || [ "$DISTRO" == "sle-hpc" ] || [ "$DISTRO" == "sles_sap" ] || [ "$DISTRO" == "opensuse-leap" ]; then
        DISTRO_FAMILY="sles"
	print_green "$DISTRO"
	/usr/bin/sudo rpm -e $(rpm -qa --queryformat "%{NAME}\n" | grep -e '[Tt]anium[Cc]lient')
	/usr/bin/sudo rm -rf /opt/Tanium
    else
        print_red "unsupported distro $DISTRO $VERSION" $ERR_UNSUPPORTED_DISTRO
    fi

    log_info "[>] detected: $DISTRO $VERSION $VERSION_NAME ($DISTRO_FAMILY)"
    print_red "*****************   TANIUM   *****************************"
    printf "\n"
}

desinstallationAgentSite24X7() {
    print_red "*****************   SITE24X7   *****************************"
    print_green "Désinstallation de l'agent Site24X7 en cours..."
    /usr/bin/sudo /opt/site24x7/monagent/bin/uninstall
    /usr/bin/sudo rm -rf /opt/site24x7/
    print_red "*****************   SITE24X7   *****************************"
    printf "\n"
}

desinstallationAgentMDATPDebian() {
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    print_green "Désinstallation de l'agent MDATP en cours..."
    /usr/bin/sudo systemctl stop mdatp
    /usr/bin/sudo apt remove mdatp -y
    /usr/bin/sudo rm -rf /opt/script_postinstall/MDATP
    /usr/bin/sudo rm -rf /opt/microsoft
    /usr/bin/sudo rm -rf /etc/apt/sources.list.d/microsoft-"$CHANNEL".list
    /usr/bin/sudo apt autoremove -y
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    printf "\n"
}

desinstallationAgentMDATPRedhat() {
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    print_green "Désinstallation de l'agent MDATP en cours..."
    /usr/bin/sudo systemctl stop mdatp
    /usr/bin/sudo yum remove mdatp -y
    /usr/bin/sudo rm -rf /opt/script_postinstall/MDATP
    /usr/bin/sudo rm -rf /opt/microsoft
    /usr/bin/sudo yum autoremove
    /usr/bin/sudo yum-config-manager --disable packages-microsoft-com-fast-"$CHANNEL"
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    printf "\n"
}

desinstallationAgentMDATPOpensuse() {
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    print_green "Désinstallation de l'agent MDATP en cours..."
    /usr/bin/sudo systemctl stop mdatp
    systemctl stop packagekit
    systemctl disable --now packagekit
    zypper --non-interactive rm packagekit
    /usr/bin/sudo zypper --non-interactive rm mdatp
    /usr/bin/sudo rm -rf /opt/script_postinstall/MDATP
    /usr/bin/sudo rm -rf /opt/microsoft
    /usr/bin/sudo zypper --non-interactive mr -d packages-microsoft-com-fast-"$CHANNEL"
    /usr/bin/sudo zypper --non-interactive rr packages-microsoft-com-fast-"$CHANNEL"
    print_red "*****************   MICROSOFT DEFENDER   *******************"
    printf "\n"
}

desinstallationAgentMDATP() {
    if [ -f /etc/os-release ] || [ -f /etc/mariner-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
        VERSION_NAME=$VERSION_CODENAME
    elif [ -f /etc/redhat-release ]; then
        if [ -f /etc/oracle-release ]; then
            DISTRO="ol"
        elif [[ $(grep -o -i "Red\ Hat" /etc/redhat-release) ]]; then
            DISTRO="rhel"
        elif [[ $(grep -o -i "Centos" /etc/redhat-release) ]]; then
            DISTRO="centos"
        fi
        VERSION=$(grep -o "release .*" /etc/redhat-release | cut -d ' ' -f2)
    else
        print_red "unable to detect distro" $ERR_UNSUPPORTED_DISTRO
    fi

    # change distro to ubuntu for linux mint support
    if [ "$DISTRO" == "linuxmint" ]; then
        DISTRO="ubuntu"
    fi

    if [ "$DISTRO" == "debian" ] || [ "$DISTRO" == "ubuntu" ]; then
        DISTRO_FAMILY="debian"
	print_green "$DISTRO_FAMILY"
	desinstallationAgentMDATPDebian
    elif [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "ol" ] || [ "$DISTRO" == "fedora" ] || [ "$DISTRO" == "amzn" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
        DISTRO_FAMILY="fedora"
	print_green "$DISTRO"
	desinstallationAgentMDATPRedhat
    elif [ "$DISTRO" == "mariner" ]; then
        DISTRO_FAMILY="mariner"
    elif [ "$DISTRO" == "sles" ] || [ "$DISTRO" == "sle-hpc" ] || [ "$DISTRO" == "sles_sap" ] || [ "$DISTRO" == "opensuse-leap" ]; then
        DISTRO_FAMILY="sles"
	print_green "$DISTRO"
	desinstallationAgentMDATPOpensuse
    else
        print_red "unsupported distro $DISTRO $VERSION" $ERR_UNSUPPORTED_DISTRO
    fi

    log_info "[>] detected: $DISTRO $VERSION $VERSION_NAME ($DISTRO_FAMILY)"
}

executeCommand() {
	if [ "$AGENT_NONROOT" == "1" ]; then
		isNonRootUser
		print_red "Connect as ROOT USER to uninstall agent"
		printf "\n"
	else
		isRootUser
		print_green "You can uninstall agent, you are root..."
		printf "\n"
	fi
	checkForBinSupport
	echo ""
	desinstallationAgentTanium
	desinstallationAgentSite24X7
	desinstallationAgentMDATP
	deleteDirPostInstall
}

main() {
	install_agent=$BOOL_TRUE
	if [ "$install_agent" = $BOOL_TRUE ]; then
		executeCommand
		print_green "Désinstallation terminée."
		printf "\n"
		print_done
	fi
}

main "$@"
