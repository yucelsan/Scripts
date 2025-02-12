#!/bin/bash
# - PostInstall Linux Script 
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
yum=`which yum 2>/dev/null`
apt=`which apt 2>/dev/null`
zypper=`which zypper 2>/dev/null`

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

    if [ -f /etc/os-release ]; then
	source /etc/os-release
	if [ -n "$PRETTY_NAME" ]; then
	    print_green "Nom du système : $PRETTY_NAME"
	fi
    fi

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

creationPostInstallDir() {
    mkdir /opt/script_postinstall
}

installationAgentTanium() {
    print_red "*****************   TANIUM   *****************************"
    print_green "Création de l'arborescence Tanium pour l'installation..."
    printf "\n"
    cd /opt/script_postinstall
    mkdir Tanium
    cd Tanium
    print_green "Téléchargement de l'agent Tanium en cours..."
    wget https://ftp.yucelsan.fr/scripts/linux-client-bundle.zip
    print_green "Unzip Tanium Linux Client Bundle en cours..."
    ${yum}${apt}${zypper} install zip -y
    unzip linux-client-bundle.zip
    /usr/bin/sudo chmod +x install.sh
    print_green "Installation de l'agent Tanium en cours..."
    /usr/bin/sudo ./install.sh
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
    elif [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "ol" ] || [ "$DISTRO" == "fedora" ] || [ "$DISTRO" == "amzn" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
        DISTRO_FAMILY="fedora"
	if  [[ "$VERSION" == 9 && "$DISTRO" == "centos" ]]; then
	    rpm -i TaniumClient-7.6.1.6481-1.rhe9.x86_64.rpm
	fi
    fi
    /usr/bin/sudo systemctl start taniumclient
    /usr/bin/sudo systemctl status taniumclient
    print_red "*****************   TANIUM   *****************************"
    printf "\n"
}

installationAgentSite24X7() {
    print_red "*****************   SITE24X7   *****************************"
    print_green "Création de l'arborescence pour l'installation agent site24X7..."
    cd /opt/script_postinstall
    mkdir Site24X7
    cd Site24X7
    print_green "Téléchargement de l'agent Site24X7..."
    wget https://staticdownloads.site24x7.com/server/Site24x7InstallScript.sh
    /usr/bin/sudo chmod +x Site24x7InstallScript.sh
    print_green "Installation de l'agent Site24X7..."
    /usr/bin/sudo bash Site24x7InstallScript.sh -i -key=us_XXXXXXXXXXXXXXXXXXXXXXXXXXX -automation=true
    /usr/bin/sudo systemctl start site24x7monagent
    /usr/bin/sudo systemctl enable site24x7monagent
    /usr/bin/sudo systemctl status site24x7monagent
    print_red "*****************   SITE24X7   *****************************"
    printf "\n"
}

installationAgentMDATPDebian() {
    print_red "**********   MICROSOFT DEFENDER ATP  *****************"
    print_green "Création de l'arborescence MDATP pour l'installation..."
    printf "\n"
    cd /opt/script_postinstall
    mkdir MDATP
    cd MDATP
    print_green "Installation des dépendances et update..."
    apt install curl libplist-utils gpg apt-transport-https python3 -y
    apt-get update -y
    print_green "Téléchargement de l'agent OMS en cours..."
    local LV_VERSION=$(echo "$VERSION" | cut -f1 -d\.)
    curl -o microsoft.list https://packages.microsoft.com/config/debian/"$LV_VERSION"/"$CHANNEL".list
    mv ./microsoft.list /etc/apt/sources.list.d/microsoft-"$CHANNEL".list
    #curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null
    #curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-"$CHANNEL".gpg
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /usr/share/keyrings/microsoft-"$CHANNEL".gpg > /dev/null
    apt-get update -y
    print_green "Installation de mdatp..."
    apt-get install mdatp -y
    wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.py
    if [ ! -f /opt/script_postinstall/MDATP/MicrosoftDefenderATPOnboardingLinuxServer.py ]; then
	wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.txt
	mv MicrosoftDefenderATPOnboardingLinuxServer.txt MicrosoftDefenderATPOnboardingLinuxServer.py
    fi
    chmod +x MicrosoftDefenderATPOnboardingLinuxServer.py
    python3 MicrosoftDefenderATPOnboardingLinuxServer.py
    curl -o /opt/script_postinstall/MDATP/eicar.com.txt https://www.eicar.org/download/eicar.com.txt
    mdatp health --field org_id
    mdatp health --field healthy
    mdatp health --field real_time_protection_enabled
    mdatp log level set --level info
    mdatp threat list
    mdatp version
    systemctl start mdatp
    systemctl status mdatp
    print_red "**********   MICROSOFT DEFENDER ATP   *****************"
    printf "\n"
}

installationAgentMDATPRedhat() {
    print_red "**********   MICROSOFT DEFENDER ATP  *****************"
    print_green "Création de l'arborescence MDATP pour l'installation..."
    printf "\n"
    cd /opt/script_postinstall
    mkdir MDATP
    cd MDATP
    print_green "Installation des dépendances et install mdatp..."
    local LV_VERSION=$(echo "$VERSION" | cut -f1 -d\.)
    yum-config-manager --add-repo=https://packages.microsoft.com/config/"$DISTRO"/"$LV_VERSION"/"$CHANNEL".repo
    rpm --import http://packages.microsoft.com/keys/microsoft.asc
    yum install mdatp -y
    yum --enablerepo=packages-microsoft-com-"$CHANNEL" install mdatp -y
    print_green "Téléchargement du script MDATP en cours..."
    wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.py
    if [ ! -f /opt/script_postinstall/MDATP/MicrosoftDefenderATPOnboardingLinuxServer.py ]; then
	wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.txt
	mv MicrosoftDefenderATPOnboardingLinuxServer.txt MicrosoftDefenderATPOnboardingLinuxServer.py
    fi
    chmod +x MicrosoftDefenderATPOnboardingLinuxServer.py
    python3 MicrosoftDefenderATPOnboardingLinuxServer.py
    curl -o /opt/script_postinstall/MDATP/eicar.com.txt https://www.eicar.org/download/eicar.com.txt
    mdatp health --field org_id
    mdatp health --field healthy
    mdatp health --field real_time_protection_enabled
    mdatp log level set --level info
    mdatp threat list
    mdatp version
    systemctl start mdatp
    systemctl status mdatp
    print_red "**********   MICROSOFT DEFENDER ATP   *****************"
    printf "\n"
}

installationAgentMDATPOpensuse() {
    print_red "**********   MICROSOFT DEFENDER ATP  *****************"
    print_green "Création de l'arborescence MDATP pour l'installation..."
    printf "\n"
    cd /opt/script_postinstall
    mkdir MDATP
    cd MDATP
    print_green "Installation des dépendances et install mdatp..."
    systemctl stop packagekit
    systemctl disable --now packagekit
    local LV_VERSION=$(echo "$VERSION" | cut -f1 -d\.)
    zypper --non-interactive addrepo -c -f -n microsoft-prod https://packages.microsoft.com/config/"$DISTRO_FAMILY"/"$LV_VERSION"/"$CHANNEL".repo
    rpm --import https://packages.microsoft.com/keys/microsoft.asc
    zypper --non-interactive install mdatp
    zypper repos
    zypper --non-interactive install packages-microsoft-com-"$CHANNEL":mdatp
    print_green "Téléchargement du script MDATP en cours..."
    wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.py
    if [ ! -f /opt/script_postinstall/MDATP/MicrosoftDefenderATPOnboardingLinuxServer.py ]; then
	wget https://ftp.yucelsan.fr/scripts/MicrosoftDefenderATPOnboardingLinuxServer.txt
	mv MicrosoftDefenderATPOnboardingLinuxServer.txt MicrosoftDefenderATPOnboardingLinuxServer.py
    fi
    chmod +x MicrosoftDefenderATPOnboardingLinuxServer.py
    python3 MicrosoftDefenderATPOnboardingLinuxServer.py
    curl -o /opt/script_postinstall/MDATP/eicar.com.txt https://www.eicar.org/download/eicar.com.txt
    mdatp health --field org_id
    mdatp health --field healthy
    mdatp health --field real_time_protection_enabled
    mdatp log level set --level info
    mdatp threat list
    mdatp version
    systemctl start mdatp
    systemctl status mdatp
    print_red "**********   MICROSOFT DEFENDER ATP   *****************"
    printf "\n"
}

installationAgentMDATP() {
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
	installationAgentMDATPDebian
    elif [ "$DISTRO" == "rhel" ] || [ "$DISTRO" == "centos" ] || [ "$DISTRO" == "ol" ] || [ "$DISTRO" == "fedora" ] || [ "$DISTRO" == "amzn" ] || [ "$DISTRO" == "almalinux" ] || [ "$DISTRO" == "rocky" ]; then
        DISTRO_FAMILY="fedora"
	print_green "$DISTRO"
	installationAgentMDATPRedhat
    elif [ "$DISTRO" == "mariner" ]; then
        DISTRO_FAMILY="mariner"
    elif [ "$DISTRO" == "sles" ] || [ "$DISTRO" == "sle-hpc" ] || [ "$DISTRO" == "sles_sap" ] || [ "$DISTRO" == "opensuse-leap" ]; then
        DISTRO_FAMILY="sles"
	print_green "$DISTRO"
	installationAgentMDATPOpensuse
    else
        print_red "unsupported distro $DISTRO $VERSION" $ERR_UNSUPPORTED_DISTRO
    fi

    log_info "[>] detected: $DISTRO $VERSION $VERSION_NAME ($DISTRO_FAMILY)"
}

changeSudoPasswd() {
    /usr/bin/sudo echo -e "PASSWD##\nPASSWD##\n" | passwd
    /usr/bin/sudo passwd -e root
}

installAgent() {
	if [ "$AGENT_NONROOT" == "1" ]; then
		isNonRootUser
		print_red "Connect as ROOT USER for installation"
		printf "\n"
	else
		isRootUser
		print_green "You can install agent, you are root..."
		printf "\n"
	fi
	checkForBinSupport
	echo ""
	creationPostInstallDir
	installationAgentTanium
	installationAgentSite24X7
	installationAgentMDATP
}

main() {
	install_agent=$BOOL_TRUE
	if [ "$install_agent" = $BOOL_TRUE ]; then
		installAgent
		print_green "Installation terminé."
		printf "\n"
#		print_green "SUDO ENTER YOUR NEW PASSWORD :"
#		changeSudoPasswd
		print_green "End of Script."
		print_done
	fi
}

main "$@"
