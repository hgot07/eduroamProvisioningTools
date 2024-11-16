#!/usr/bin/perl
#
# eduroam Provisioning Tools
#  Simple CGI script for eduroam profile provisioning
#  Target: ChromeOS
# 
# Usage:
#  - Customize the configuration part below and the external file
#    etc/eduroam-common.cfg.
#  - Put this script on a web server as a CGI program.
#    (Please refer to the HTTP server's manual for configuring CGI.)
#  - Access https://<path_to_script>/eduroam-onc.cgi.
# Notes:
#  - User needs to open chrome://network on Chrome browser and load
#    the downloaded eduroam-config.onc file manually.
# References:
#  - Open Network Configuration
#    https://chromium.googlesource.com/chromium/src/+/main/components/onc/docs/onc_spec.md
#
# 20230712 Hideaki Goto (Tohoku University and eduroam JP)
# 20241117 Hideaki Goto (Tohoku University and eduroam JP)
#	Add EAP-TLS support.
#

use CGI;
use DateTime;
use MIME::Base64;
use Data::UUID;


#---- Configuration part ----

# include common settings
require '../etc/eduroam-common.cfg';

#### Add your own code here to set ID/PW. ####
#$userID = 'name@example.com';
#$passwd = 'somePassword';

# External code that sets $userID, $passwd, and optionally $ExpirationDate
require '../etc/getuserinfo.pl';
if ( &getuserinfo( $ENV{'REMOTE_USER'} ) ){ exit(1); }

$uname = $anonID = $userID;
$anonID =~ s/^.*\@/anonymous@/;

$InnerMethod = "MSCHAPv2";
$OuterMethod = "PEAP";
#$OuterMethod = "EAP-TTLS";


#---- Profile composition part ----
# (no need to edit below, hopefully)

# Fix certificate format
chomp $client_cert_np;
$client_cert_np =~ s/[\r\n]//g;
$client_cert_np =~ s/\//\\\//g;
$client_cert_np =~ s/\s+//g;

$ts=DateTime->now->datetime."Z";

my $uuid1 = Data::UUID->new->create_str();
$uuid1 = uc $uuid1;
my $uuid_s = Data::UUID->new->create_str();
$uuid_s = uc $uuid_s;
my $uuid_c = Data::UUID->new->create_str();
$uuid_c = uc $uuid_c;

$xml_cert = '';
if ( $CAfile ne '' ){
$cert = '';
	open my $fh, '<', $CAfile;
	while(<$fh>){
		if ( $_ =~ /BEGIN\s+CERTIFICATE/ ){ next; }
		if ( $_ =~ /END\s+CERTIFICATE/ ){ last; }
		$cert .= $_;
	}
	close $fh;
	chomp $cert;
	$cert =~ s/[\r\n]//g;
	$cert =~ s/\//\\\//g;
}


if ( $client_cert_np ){

$xml = <<"EOS";
{
    "Type": "UnencryptedConfiguration",
    "Certificates": [
        {
            "GUID": "{$uuid_s}",
            "Remove": false,
            "Type": "Authority",
            "X509": "$cert"
        },
        {
            "GUID": "{$uuid_c}",
            "Remove": false,
            "Type": "Client",
            "PKCS12": "$client_cert_np"
        }
    ],
    "NetworkConfigurations": [
        {
            "GUID": "$uuid1",
            "Name": "$SSID",
            "Remove": false,
            "Type": "WiFi",
            "WiFi": {
                "AutoConnect": true,
                "EAP": {
                    "ClientCertType": "Ref",
                    "ClientCertRef": "$uuid_c",
                    "Identity": "$anonID",
                    "Outer": "EAP-TLS",
                    "ServerCARefs": [
                        "{$uuid_s}"
                    ],
                    "UseSystemCAs": true,
                    "SubjectAlternativeNameMatch": [
                        {
                            "Type": "DNS",
                            "Value": "$AAAFQDN"
                        }
                    ]
                },
                "HiddenSSID": false,
                "SSID": "$SSID",
                "Security": "WPA-EAP"
            },
            "ProxySettings": {
                "Type": "WPAD"
            }
        }
    ]
}
EOS

}
else {

$xml = <<"EOS";
{
    "Type": "UnencryptedConfiguration",
    "Certificates": [
        {
            "GUID": "{$uuid_s}",
            "Remove": false,
            "Type": "Authority",
            "X509": "$cert"
        }
    ],
    "NetworkConfigurations": [
        {
            "GUID": "$uuid1",
            "Name": "$SSID",
            "Remove": false,
            "Type": "WiFi",
            "WiFi": {
                "AutoConnect": true,
                "EAP": {
                    "AnonymousIdentity": "$anonID",
                    "Identity": "$userID",
                    "Password": "$passwd",
                    "Outer": "$OuterMethod",
                    "Inner": "$InnerMethod",
                    "SaveCredentials": true,
                    "ServerCARefs": [
                        "{$uuid_s}"
                    ],
                    "UseSystemCAs": true,
                    "SubjectAlternativeNameMatch": [
                        {
                            "Type": "DNS",
                            "Value": "$AAAFQDN"
                        }
                    ]
                },
                "HiddenSSID": false,
                "SSID": "$SSID",
                "Security": "WPA-EAP"
            },
            "ProxySettings": {
                "Type": "WPAD"
            }
        }
    ]
}
EOS

}

print <<"EOS";
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="eduroam-config.onc"

$xml
EOS

exit(0);


