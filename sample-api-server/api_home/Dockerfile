FROM ubuntu:xenial
RUN apt-get update

RUN apt-get install --no-install-recommends -y apache2 libapache2-mod-python software-properties-common 
RUN add-apt-repository ppa:certbot/certbot
RUN apt-get update
RUN apt-get install -y --no-install-recommends python-certbot-apache 
RUN a2enmod ssl cgi rewrite proxy_http

## Clean out all the apt-stuff to reduce the image size
RUN apt-get clean
RUN rm -rf /var/cache/apt 
RUN rm -rf /var/lib/dpkg/info/* 
RUN rm -rf /var/lib/apt/lists/* 

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]