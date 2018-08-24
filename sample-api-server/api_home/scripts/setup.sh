#!/bin/bash
if [ $0 != "/root/scripts/setup.sh" ]; then
	echo "Script will not execute outside of Docker context."
	exit
fi
/usr/bin/apt-get update
/usr/bin/apt-get install -y apache2 libapache2-mod-python software-properties-common tzdata
/usr/bin/add-apt-repository -y ppa:certbot/certbot
/usr/bin/apt-get update
/usr/bin/apt-get install -y python-certbot-apache 
/usr/sbin/a2enmod ssl cgi rewrite proxy_http allowmethods
/usr/bin/certbot --apache --email $CERTBOT_EMAIL -d $CERTBOT_HOSTNAME --agree-tos --non-interactive
/usr/sbin/a2ensite 0-api.conf
/usr/sbin/a2ensite 1-api-80.conf
/usr/sbin/a2ensite 2-api-internal.conf
/usr/sbin/a2ensite 3-api-internal-80.conf
/usr/sbin/a2dissite 000-default
/usr/sbin/a2dissite 000-default-le-ssl

/bin/chown -R www-data: /var/www/state
/bin/chown -R www-data: /var/log/apache2

Copy_ServerName=`/bin/egrep -o '^ServerName.*$' /etc/apache2/sites-available/000-default-le-ssl.conf`
/bin/sed -i "s|##ServerName##|$Copy_ServerName|" /etc/apache2/sites-available/0-api.conf 
/bin/sed -i "s|##ServerName##|$Copy_ServerName|" /etc/apache2/sites-available/1-api-80.conf 
Copy_SSLCertificateFile=`/bin/egrep -o '^SSLCertificateFile.*$' /etc/apache2/sites-available/000-default-le-ssl.conf`
/bin/sed -i "s|##SSLCertificateFile##|$Copy_SSLCertificateFile|" /etc/apache2/sites-available/0-api.conf 
Copy_SSLCertificateKeyFile=`/bin/egrep -o '^SSLCertificateKeyFile.*$' /etc/apache2/sites-available/000-default-le-ssl.conf`
/bin/sed -i "s|##SSLCertificateKeyFile##|$Copy_SSLCertificateKeyFile|" /etc/apache2/sites-available/0-api.conf
Copy_Include=`/bin/egrep -o '^Include.*$' /etc/apache2/sites-available/000-default-le-ssl.conf`
/bin/sed -i "s|##Include##|$Copy_Include|" /etc/apache2/sites-available/0-api.conf 



