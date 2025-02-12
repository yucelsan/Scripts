#!/bin/bash

#PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:/usr/sfw/bin:$PATH
SUCCESS=0
WARNING=1
FAILURE=2
AGENT_NONROOT='0'
vtom_directory="/opt/vtom"
filetmp1="/tmp/install_vtom"
filetmp2="/tmp/install_vtom.ini"
filetmp3="/tmp/VT-CS-LINUX_X64.71.Z"
vtomfile1="/opt/vtom/install_vtom"
vtomfile2="/opt/vtom/install_vtom.ini"
vtomfile3="/opt/vtom/VT-CS-LINUX_X64.71.Z"
vtomfileadmin="/opt/vtom/admin/.vtom.ini"
io_vtom_script="/opt/vtom/io_vtom_install.log"

print_green() {
    printf "\033[32m%s\033[0m\n" "$*"
}

print_red() {
    printf "\033[31m%s\033[0m\n" "$*"
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

edit_vtom_ini() {
	if [ -f "$vtomfile2" ]; then
		sed -i 's|tom_home=.*|tom_home=/opt/vtom|' $vtomfile2
	else
		print_red "/opt/vtom/install_vtom.ini File not exist."
		printf "\n"
		exit $FAILURE
	fi
}

vtom_admin() {
	if [ -f "$vtomfileadmin" ]; then
		sed -i '/\[BDAEMON\]/,/^\[/ {
        	s/^;TRACE_LEVEL=.*/TRACE_LEVEL=6/
        	s|^;TRACE_FILE=.*|TRACE_FILE=/opt/vtom/traces/bdaemon.log|
        	s/^;TRACE_FILE_SIZE=.*/TRACE_FILE_SIZE=10/
        	s/^;TRACE_FILE_COUNT=.*/TRACE_FILE_COUNT=10/
    	}' $vtomfileadmin
    else
    	print_red "/opt/vtom/admin/.vtom.ini File not exist."
		printf "\n"
		exit $FAILURE
	fi
	# sed -i 's|;TRACE_LEVEL=.*|TRACE_LEVEL=6|' $vtomfileadmin
	# sed -i 's|;TRACE_FILE=.*|TRACE_FILE=/opt/vtom/traces/bdaemon.log|' $vtomfileadmin
	# sed -i 's|;TRACE_FILE_SIZE=.*|TRACE_FILE_SIZE=10|' $vtomfileadmin
	# sed -i 's|;TRACE_FILE_COUNT=.*|TRACE_FILE_COUNT=10|' $vtomfileadmin
}

services_port_copy() {
	echo "tomDBd          30001/tcp               # VTOM" >> /etc/services
	echo "bdaemon         30004/tcp               # VTOM" >> /etc/services
	echo "sbdaemon        30014/tcp               # VTOM" >> /etc/services
	echo "vtserver        30007/tcp               # VTOM" >> /etc/services
	echo "svtserver       30017/tcp               # VTOM" >> /etc/services
	echo "vtmanager       30000/tcp               # VTOM" >> /etc/services
	echo "svtmanager      30010/tcp               # VTOM" >> /etc/services
}

vtom_install() {
	if [ "$AGENT_NONROOT" == "1" ]; then
		isNonRootUser
		print_red "Connect as ROOT USER to launch script..." >> $io_vtom_script
		printf "\n"
	else
		isRootUser
		print_green "You can launch script, you are root..." >> $io_vtom_script
		printf "\n"
	fi
	if [ ! -d "$vtom_directory" ]; then
		mkdir /opt/vtom
	else
		print_red "VTOM installation directory exist."
		printf "\n"
		exit $FAILURE
	fi
	if [ ! -f "$io_vtom_script" ]; then
		touch /opt/vtom/io_vtom_install.log
	fi
	apt-get install ksh -y >> $io_vtom_script
	useradd -d /home/vtom -m -s /usr/bin/ksh vtom >> $io_vtom_script
	chown -R vtom:vtom /opt/vtom/ >> $io_vtom_script
	cd /opt/vtom
	pwd >> $io_vtom_script
	if [ -f "$filetmp1" ]; then
		mv /tmp/install_vtom /opt/vtom
	else
		print_red "File not exist. upload install_vtom file in /tmp and try again."
		printf "\n"
		exit $FAILURE
	fi
	if [ -f "$filetmp2" ]; then
		mv /tmp/install_vtom.ini /opt/vtom
	else
		print_red "File not exist. upload install_vtom.ini file in /tmp and try again."
		printf "\n"
		exit $FAILURE
	fi
	if [ -f "$filetmp3" ]; then
		mv /tmp/VT-CS-LINUX_X64.71.Z /opt/vtom
	else
		print_red "File not exist. upload VT-CS-LINUX_X64.71.Z file in /tmp and try again."
		printf "\n"
		exit $FAILURE
	fi
	chmod +x $vtomfile1
	edit_vtom_ini >> $io_vtom_script
	./install_vtom VT-CS-LINUX_X64.71.Z >> $io_vtom_script
	cd /opt/vtom/admin/
	pwd >> $io_vtom_script

	vtom_admin >> $io_vtom_script
	cp /etc/services /tmp/services.backup
	services_port_copy >> $io_vtom_script
	su - vtom -c "cd /opt/vtom/admin/" >> $io_vtom_script
	su - vtom -c "/opt/vtom/admin/stop_client" >> $io_vtom_script
	su - vtom -c "/opt/vtom/admin/start_client" >> $io_vtom_script
	cat /etc/services | grep -i "vtom" >> $io_vtom_script
	cat /opt/vtom/admin/services.new >> $io_vtom_script
	print_green "cat /opt/vtom/io_vtom_install.log to see your installation result."
	printf "\n"
}

main() {
    vtom_install
    print_green "Opération terminée."
    printf "\n"
}

main "$@"