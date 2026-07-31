#!/usr/bin/env bash

set -e

# Assumes Let's Encrypt

if [ $# -ne 1 -a $# -ne 3 ]; then
	echo "usage: ${0%%*/} <domain> [<keystore> <password>]"
	exit 2
fi

domain=$1
keystore=${2:-core-api.keystore}
pass=${3:-kspassword}

LEdirs=(/usr/local/etc /etc /opt .)
for LEdir in "${LEdirs[@]}"; do
	srcdir="${LEdir}/letsencrypt/live/${domain}"
	if [ -d "$srcdir" ]; then
		echo "Using certs & keys from ${srcdir}"
		break;
	fi
	unset srcdir
done

if [ -z "${srcdir}" ]; then
	echo "Can't find Let's Encrypt folder for ${domain}"
	exit
fi

# key & cert
rm -f "${domain}.p12"
openssl pkcs12 \
	-inkey "${srcdir}/privkey.pem" -in "${srcdir}/fullchain.pem" \
	-export -out "${domain}.p12" -passout pass:"${pass}" \
	-name "${domain}"

rm -f "${keystore}"
keytool -importkeystore -noprompt \
	-srckeystore "${domain}.p12" -srcstoretype PKCS12 -srcstorepass "${pass}" \
	-destkeystore "${keystore}" -deststorepass "${pass}" -destkeypass "${pass}" \
	-alias "${domain}"

printf "Built keystore: ${keystore}, with password: ${pass}\nFor settings.json:\n"

printf "\tsslKeystorePathname: \"%s\",\n" "${keystore}"
printf "\tsslKeystorePassword: \"%s\",\n" "${pass}"
