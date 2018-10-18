### A sample backend API server for the *aws-auto-scaling-custom-resource* parent project.  
*Contributed by Sean Greathouse*  

This project implements a sample api server that satisfies the requirements of the 
*Test your REST Endpoint URL* step in *[aws-auto-scaling-custom-resource/README.md](../README.md)*  
It is intended as an example, but can be modified for production use.  
  
#### The project provides:
- Dockerized API server using Apache and Python  
- Scripted setup  
- Automated provisioning of SSL certificates from [Let's Encrypt](https://letsencrypt.org)
- Demo mode to auto-rotate through application scaling states  
- Production mode to enable integration with your custom scaling system  
  
#### Host system requirements:  
- Docker (tested on Docker CE 18)
- Inbound port 80 & 443 open to the internet  
- A valid dns A or CNAME record pointing to your host system  
- The host may not run any other process listening on ports 80 or 443


---
### Setup Guide  
  
From your host system:    

Set the $API_HOME environment variable to the default or your preferred directory.  
*This variable is required in subsequent commands.  Consider setting it as a permanent environment variable.*   
`API_HOME=~/api_home`   

Clone the repository and build your api\_home working directory    
```bash
git clone git@github.com:aws/aws-auto-scaling-custom-resource.git 
cd aws-auto-scaling-custom-resource/sample-api-server  
mkdir $API_HOME
cp -Rp api_home/* $API_HOME  
cd $API_HOME 
```
Pull the Docker base image  
```bash
docker pull ubuntu:xenial
```   

Set environment variables for SSL cert creation  
*CERTBOT_HOSTNAME must match the dns entry for your host*  
*CERTBOT_EMAIL* will be used by Let\'s Encrypt to notify you of certificate expiration  

```bash
CERTBOT_EMAIL="foo@example.com"    
CERTBOT_HOSTNAME="api.example.com"  
```

Docker run to populate the directories in *api\_home* with apache config and ssl certificates.  
All system config, state, and logs are stored in these directories on your local host.  
```bash
docker run --rm -p 80:80 -it --name api_build_static \
-v "$API_HOME"/var/www:/var/www -v "$API_HOME"/var/log/apache2:/var/log/apache2 \
-v "$API_HOME"/etc/apache2:/etc/apache2 -v "$API_HOME"/usr/lib/cgi-bin:/usr/lib/cgi-bin  \
-v "$API_HOME"/etc/letsencrypt:/etc/letsencrypt -v "$API_HOME"/scripts:/root/scripts \
--env CERTBOT_EMAIL="$CERTBOT_EMAIL" --env CERTBOT_HOSTNAME="$CERTBOT_HOSTNAME" \
ubuntu:xenial /root/scripts/setup.sh
```

Build the Docker image for the api server  
`docker build $API_HOME/ -t api_image`    

Run the Docker image as a daemonized container  
* Listening on ports 80 & 443  
* Mounting config, docroot, log and cgi directories from localhost over the same directories in the Docker container.   
*Note that the container will not run automatically at system startup.*  
```bash
docker run --rm -p 80:80 -p 443:443 -d --name api \
-v "$API_HOME"/var/www:/var/www -v "$API_HOME"/var/log/apache2:/var/log/apache2 \
-v "$API_HOME"/etc/apache2:/etc/apache2 -v "$API_HOME"/usr/lib/cgi-bin:/usr/lib/cgi-bin  \
-v "$API_HOME"/etc/letsencrypt:/etc/letsencrypt \
api_image
```

To test your installation call the following url from a browser (replacing the hostname with your own)   
`https://api.example.com/v1/scalableTargetDimensions/1-23456789`  
you should see a json response:   
```
{"scalableTargetDimensionId": "10", "scalingStatus": "Successful", "resourceName": "MyService", "desiredCapacity": 1.0, "actualCapacity": 1.0, "dimensionName": "MyDimension", "version": "MyVersion"}
```   

If the above fails, test without https  
`http://api.example.com/v1/scalableTargetDimensions/1-23456789`  
You can also test from the command line of your host  
`curl http://localhost/v1/scalableTargetDimensions/1-23456789`    
If that fails, you can test to see if the Docker container is running   
`docker ps`   
And if Apache is working on port 80   
`curl localhost`   

---
### Host certificate setup  

*Once you require host certificates for your api backend, you will no longer be able to test your api over https.  
If your outbound network allows unencrypted PATCH commands you can test over http.  
However, the following setup is not required for the integration to work so you can leave this step until after testing the full system.*   

Get the certificate file you pulled pulled from API Gateway in the 
*Configure SSL/HTTPS* section of *[aws-auto-scaling-custom-resource](../README.md)*  
The certificate should look like the following (with more text between the BEGIN and END lines):    
```
-----BEGIN CERTIFICATE-----
MIIC6TCCAdGgAwIBAgIJAKumXi6NTmSBMA0GCSqGSIb3DQEBCwUAMDQxCzAJBgNV
BAYTAlVTMRAwDgYDVQQHEwdTZWF0dGxlMRMwEQYDVQQDEwpBcGlHYXRld2F5MB4X
EcQhaxYT710cDFtf9kkbzTQMt0os4mKuItILvKQ.......
-----END CERTIFICATE----- 
``` 

Edit the client certificate public key file and paste in the certificate  
`vim $API_HOME/etc/apache2/public-keys/ProdClientCertificate.pem`   

To require host certificate verification edit the Apache config file for the HTTPS Virtual Host  
`vim $API_HOME/etc/apache2/sites-available/0-api.conf`  
un-comment the following lines and save the file    
```
#SSLVerifyClient none
#SSLCACertificateFile "public-keys/ProdClientCertificate.pem"
#<Location "/v1/scalableTargetDimensions/">
#SSLVerifyClient require
#SSLVerifyDepth 1
#</Location> 
```
then restart Apache in the container  
`docker exec api /usr/sbin/apachectl restart`      

 ---
 ### Testing api backend scaling responses
 
 When AWS Auto Scaling calls the API to initiate a scaling event it issues an https PATCH call with the new desired capacity.    
 To test directly in Postman, send a PATCH request to:   
 `http://api.example.com/v1/scalableTargetDimensions/1-23456789`   
 with a body payload of:   
 `{"desiredCapacity":2.0}`  
 The *1-23456789* in the URL above can be replaced by any ID.  The system can manage separate state for an arbitrary number of IDs.  
 AWS Auto Scaling will use the ID you set in the *Register a Scalable Target* section of *[aws-auto-scaling-custom-resource](../README.md)*   
 
 The system will respond by setting the *desiredCapacity* to *2.0* and *scalingStatus* to *Pending*  
 ```
{"scalingStatus": "Pending", "scalableTargetDimensionId": "1-23456789", "version": "MyVersion", "resourceName": "MyService", "actualCapacity": 1.0, "desiredCapacity": 2.0, "dimensionName": "MyDimension"}
```  
By default the system will increment the state for the *scalableTargetDimensionId* with each subsequent GET.  
- *"scalingStatus": "InProgress"*   
- *"scalingStatus": "Successful"*  - *"actualCapacity": 2.0*  

You can see the event progression in the api log (replace the *20180822* with the current host date):  
`tail -f $API_HOME/var/log/apache2/api-20180822`  

```
20180822-234725 Request: PATCH dimensionId: 1-23456789 {"desiredCapacity": 2.0}
20180822-234725 Response: dimensionId: 1-23456789  desiredCapacity: 1.0 -> 2.0  scalingStatus: Successful -> Pending
20180822-235128 Request: GET dimensionId: 1-23456789 
20180822-235128 Response: dimensionId: 1-23456789  scalingStatus: Pending -> InProgress
20180822-235303 Request: GET dimensionId: 1-23456789 
20180822-235303 Response: dimensionId: 1-23456789  actualCapacity: 1.0 -> 2.0  scalingStatus: InProgress -> Successful
```   
Now that you have verified that the backend API works, you can proceed with the *Test the Scaling Policy* section in  *[aws-auto-scaling-custom-resource](../README.md)*  and watch the AWS Auto Scaling service issue scaling commands in the API log.  

If you want to simulate a scaling failure, change the cgi scripts *testFailure* mode.  
*testFailure* works in *demoMode* by setting *scalingStatus* to *Failed* instead of *Successful* in the final scaling stage.  
`vim $API_HOME/usr/lib/cgi-bin/api.py`  
`testFailure = True`  

### Production mode / manual scaling
In a production scaling scenario, the system that does the actual application scaling will need to update the scaling state in the API.  In production mode the cgi script will still set *scalingStatus* from *Successful* to *Pending* as a response to the initial *desiredCapacity* change issued by AWS Auto Scaling.    
To set production mode:  
`vim $API_HOME/usr/lib/cgi-bin/api.py`  
`demoMode = False`  

The state of each *scalableTargetDimensionId* can be set by issuing a PATCH to the API with the appropriate json body payload. 
 ```
{"scalingStatus": "Successful", "actualCapacity": 2.0}
```   
The current implementation saves state into files in *$API_HOME/var/www/state/* on the local host.  
For an actual production system, state should be managed in a highly available data store accessible from multiple hosts.  
This change could be as simple as saving state to an NFS system, or by re-writing the *write_state* and *read_state* functions in *api.py* to talk to a NoSql key-value store.  

### Security considerations for production mode
*The following steps close security holes that are intentionally open for dev and test.  Follow your own security best practices if you deploy this system.*    
Disable port 80 on one or more layers of the system  
* Docker layer  
Remove *-p 80:80* from the *docker run* statement   
* Apache layer   
Disable the Apache VirtualHosts that listen on 80  
```bash
docker exec api /usr/sbin/a2dissite 1-api-80.conf  
docker exec api /usr/sbin/a2dissite 3-api-internal-80.conf
docker exec api /usr/sbin/apachectl restart  
```  
* Block external port 80 traffic in your firewall or AWS VPC Security Group   

Disable access to docroot by editing the relevant virtual host conf files  
```
$API_HOME/etc/apache2/sites-available/0-api.conf
$API_HOME/etc/apache2/sites-available/1-api-80.conf
$API_HOME/etc/apache2/sites-available/2-api-internal.conf
$API_HOME/etc/apache2/sites-available/3-api-internal-80.conf
```
and un-commenting the following text block   
```
#<Directory "/var/www/html/">
#       Options FollowSymLinks
#       AllowOverride None
#       Order Deny,Allow
#       Deny from All
#</Directory>
```   
Require a host certificate as documented above  
Apache only supports a single host certificate per VirtualHost so enabling host certificates in 0-api.conf will block all other https client acccess.   
You can continue to access the api by configuring an alternate dns ServerName in the *2-api-internal.conf* or *3-api-internal-80.conf* conf files.  To use https for internal api access you will need to set up valid SSL certificates.  

To auto-renew the Let's Encrypt certificate, run the following as a scheduled command on your host. 
`docker exec api /usr/bin/certbot renew`  


