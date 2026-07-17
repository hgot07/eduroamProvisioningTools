#!/usr/bin/perl
#
# eduroam Provisioning Tools
#  Simple CGI script for Wi-Fi provisioning
#  Target: ChromeOS
# 
# Usage:
#  - Customize the configuration part below and the external file
#    etc/config.ini.
#  - Put this script on a web server as a CGI program.
#    (Please refer to the HTTP server's manual for configuring CGI.)
#  - Access https://<path_to_script>/eduroam-onc.cgi.
# Notes:
#  - User needs to open chrome://network on Chrome browser and load
#    the downloaded wifi-config.onc file manually.
# References:
#  - Open Network Configuration
#    https://chromium.googlesource.com/chromium/src/+/main/components/onc/docs/onc_spec.md
#
# 20230712 Hideaki Goto (Tohoku University and eduroam JP)
# 20241117 Hideaki Goto (Tohoku University and eduroam JP)
#	Add EAP-TLS support.
# 20260715 Hideaki Goto (Tohoku University and eduroam JP)
#	Modernize.
# 20260717 Hideaki Goto (Tohoku University and eduroam JP)
#	Some fixes and feature extentions.
#

use strict;
use warnings;
use CGI::Cookie;
use DateTime;
use Digest::SHA qw(hmac_sha256 hmac_sha256_base64);
use MIME::Base64;
use Data::UUID;
use Config::Tiny;

#require '../etc/check-login.pl';
require '../etc/getuserinfo.pl';

my $time = time();

my $webuser = $ENV{'REMOTE_USER'};

my $config = Config::Tiny->read('../etc/config.ini');
if ( ! defined $config ){
print <<EOS;
Content-Type: text/plain; charset=utf-8

No configuration file found.
EOS
	exit(0);
}

my $FileName = $config->{default}->{FileName};
my $SSID = $config->{default}->{SSID};
my $AAAFQDN = $config->{default}->{AAAFQDN};
my $CAfile = $config->{default}->{CAfile};
my $cert = $config->{default}->{cert};
my $HomeDomain = $config->{default}->{HomeDomain};

my %userinfo = getuserinfo($webuser);
my $userID = $userinfo{'userID'};
if ( $userID eq '' ){ exit(1); }

my $passwd = $userinfo{'passwd'};
my $ExpirationDate = $userinfo{'ExpirationDate'};
my $client_cert_np = $userinfo{'client_cert_np'};


my $uname = $userID;
my $anonID = $userID;
$anonID =~ s/^.*\@/anonymous@/;

#my $OuterMethod = "PEAP";
#my $InnerMethod = "MSCHAPv2";
my $OuterMethod = "EAP-TTLS";
my $InnerMethod = "PAP";


#---- Profile composition part ----
# (no need to edit below, hopefully)

# Fix certificate format
chomp $client_cert_np;
$client_cert_np =~ s/[\r\n]//g;
$client_cert_np =~ s/\//\\\//g;
$client_cert_np =~ s/\s+//g;

my $ts=DateTime->now->datetime."Z";

my $uuid1 = Data::UUID->new->create_str();
$uuid1 = uc $uuid1;
my $uuid_s = Data::UUID->new->create_str();
$uuid_s = uc $uuid_s;
my $uuid_c = Data::UUID->new->create_str();
$uuid_c = uc $uuid_c;

my $xml_cert = '';
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


my $xml;
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
Content-Disposition: attachment; filename="$FileName.onc"

$xml
EOS

exit(0);


