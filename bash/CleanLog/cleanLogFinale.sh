#!/bin/bash

PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:/usr/sfw/bin:$PATH
SUCCESS=0
WARNING=1
FAILURE=2
AGENT_NONROOT='0'

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

declare -a data1

data1=("YUCELSAN-AT-Site" "YUCELSAN-AT")
data1+=("YUCELSAN-BE-Site" "YUCELSAN-BE")
data1+=("YUCELSAN-CH-Site" "YUCELSAN-CH")
data1+=("YUCELSAN-CZ-Site" "YUCELSAN-CZ")
data1+=("YUCELSAN-DE-Site" "YUCELSAN-DE")
data1+=("YUCELSAN-DK-Site" "YUCELSAN-DK")
data1+=("YUCELSAN-ES-Site" "YUCELSAN-ES")
data1+=("YUCELSAN-FR-Site" "YUCELSAN-FR")
data1+=("YUCELSAN-GB-Site" "YUCELSAN-GB")
data1+=("YUCELSAN-HU-Site" "YUCELSAN-HU")
data1+=("YUCELSAN-IT-Site" "YUCELSAN-IT")
data1+=("YUCELSAN-NL-Site" "YUCELSAN-NL")
data1+=("YUCELSAN-NO-Site" "YUCELSAN-NO")
data1+=("YUCELSAN-PL-Site" "YUCELSAN-PL")
data1+=("YUCELSAN-PT-Site" "YUCELSAN-PT")
data1+=("YUCELSAN-SE-Site" "YUCELSAN-SE")
data1+=("YUCELSAN-SK-Site" "YUCELSAN-SK")

#echo "Taille du tableau data1 : ${#data1[@]}"
#echo "Les indices sont : ${!data1[@]}"

cleanLog() {
	if [ "$AGENT_NONROOT" == "1" ]; then
		isNonRootUser
		print_red "Connect as ROOT USER to launch script..."
		printf "\n"
	else
		isRootUser
		print_green "You can launch script, you are root..."
		printf "\n"
	fi
	for (( i = 0; i < "${#data1[@]}"; i++ ))
	do
	    for (( j = 0; j < "${#data1[@]}"; j++ ))
	    do
		dirFiliale=/opt/yucelsan/server1/share/sites/"${data1[i, j]}"/units/"${data1[i,j+=1]}"/impex/log;
#		echo "${dirFiliale}"

		if [ -d "${dirFiliale}" ]; then
		    cd "${dirFiliale}";
		    pwd
		    ls | wc -l
		    print_green "Nombre de fichiers de logs restants : "
		    find . -type f -mtime +10 -exec rm {} \;
		    ls | wc -l
		else
		    print_red "Directory not found..."
		    printf "\n"
		fi

		if [ "${data1[i, j]}" == "YUCELSAN-SK" ]; then
		    exit $SUCCESS
		fi
	    done
	done
}

main() {
    cleanLog
    print_green "Opération terminée."
    printf "\n"
}

main "$@"

