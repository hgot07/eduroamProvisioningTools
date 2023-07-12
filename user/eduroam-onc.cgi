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

$ts=DateTime->now->datetime."Z";

my $uuid1 = Data::UUID->new->create_str();
$uuid1 = uc $uuid1;
my $uuid2 = Data::UUID->new->create_str();
$uuid2 = uc $uuid2;

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

my $xml = <<"EOS";
{
    "Type": "UnencryptedConfiguration",
    "Certificates": [
        {
            "GUID": "{$uuid1}",
            "Remove": false,
            "Type": "Authority",
            "X509": "$cert"
        }
    ],
    "NetworkConfigurations": [
        {
            "GUID": "$uuid2",
            "Name": "eduroam",
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
                        "{$uuid1}"
                    ],
                    "UseSystemCAs": false,
                    "SubjectAlternativeNameMatch": [
                        {
                            "Type": "DNS",
                            "Value": "$AAAFQDN"
                        }
                    ]
                },
                "HiddenSSID": false,
                "SSID": "eduroam",
                "Security": "WPA-EAP"
            },
            "ProxySettings": {
                "Type": "WPAD"
            }
        }
    ]
}
EOS

print <<"EOS";
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="eduroam-config.onc"

$xml
EOS

exit(0);


