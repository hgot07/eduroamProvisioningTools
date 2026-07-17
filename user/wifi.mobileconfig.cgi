#!/usr/bin/perl
#
# Wi-Fi Provisioning Tools
#  Simple CGI script for Wi-Fi provisioning
#  Target: iOS/iPadOS 14+, macOS 10+
# 
# Usage:
#  - Customize the configuration part below and the external file
#    etc/config.ini.
#  - Put this script on a web server as a CGI program.
#    (Please refer to the HTTP server's manual for configuring CGI.)
#  - Access https://<path_to_script>/wifi.mobileconfig.cgi.
# Notes:
#  - It is recommended to sign the configuration profile (XML), although
#    unsigned profiles can still be used.
#  - External command "openssl" is needed for the signing.
#  - The key and certificate files for signing need to be accessible
#    from the process group such as "www". (chgrp & chmod o+r)
#  - You don't need to change EncryptionType "WPA2" even if you want
#    to join a WPA3 network. Please see the References for details.
# References:
#  - Configuration Profile Reference
#    https://developer.apple.com/business/documentation/Configuration-Profile-Reference.pdf
#  - The payload for configuring Wi-Fi on the device.
#    https://developer.apple.com/documentation/devicemanagement/wifi
#
# 20220731 Hideaki Goto (Tohoku University and eduroam JP)
# 20220805 Hideaki Goto (Tohoku University and eduroam JP)
#	+ expiration date
# 20220817 Hideaki Goto (Tohoku University and eduroam JP)
#	+ cert. chain for signing
# 20220826 Hideaki Goto (Tohoku University and eduroam JP)
#	+ per-user ExpirationDate
# 20230908 Hideaki Goto (Tohoku University and eduroam JP)
#	Renamed
# 20241031 Hideaki Goto (Tohoku University and eduroam JP)
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
my $ICAfile = $config->{default}->{ICAfile};
my $ICAcertname = $config->{default}->{ICAcertname};
my $PLID = $config->{default}->{PLID};
my $PLuuid = $config->{default}->{PLuuid};
$PLuuid= uc $PLuuid;	# make sure upper case
my $PayloadDisplayName = $config->{default}->{PayloadDisplayName};
my $cert = $config->{default}->{cert};
my $Passpoint = $config->{default}->{Passpoint};
my $HomeDomain = $config->{default}->{HomeDomain};
my $RCOI = $config->{default}->{RCOI};
my $friendlyName = $config->{default}->{friendlyName};
my $description = $config->{default}->{description};
my $signercert = $config->{default}->{signercert};
my $signerchain = $config->{default}->{signerchain};
my $signerkey = $config->{default}->{signerkey};
my $NAIrealm = $config->{default}->{NAIrealm};

my %userinfo = getuserinfo($webuser);
my $userID = $userinfo{'userID'};
if ( $userID eq '' ){ exit(1); }

my $passwd = $userinfo{'passwd'};
my $ExpirationDate = $userinfo{'ExpirationDate'};
my $client_cert = $userinfo{'client_cert'};
my $client_cert_pass = $userinfo{'client_cert_pass'};
if ( $userinfo{'NAIrealm'} ){
	$NAIrealm = $userinfo{'NAIrealm'};
}
if ( $userinfo{'friendlyName'} ){
        $friendlyName = $userinfo{'friendlyName'};
}
if ( $userinfo{'PayloadDisplayName'} ){
	$PayloadDisplayName = $userinfo{'PayloadDisplayName'};
}


my $uname = $userID;
my $anonID = $userID;
$anonID =~ s/^.*@/anonymous@/;

# To omit signing, uncomment this.
#$signercert = '';
#$signerchain = '';


#---- Profile composition part ----
# (no need to edit below, hopefully)

# Fix certificate format
if ( !defined $client_cert ){
	$client_cert = '';
}
chomp($client_cert);

my $ts=DateTime->now->datetime."Z";

my $uuid1 = Data::UUID->new->create_str();
$uuid1 = uc $uuid1;
my $uuid2 = Data::UUID->new->create_str();
$uuid2 = uc $uuid2;
my $cert_uuid = Data::UUID->new->create_str();
$cert_uuid = uc $cert_uuid;

my $xml_HS20 = "\t\t\t<key>SSID_STR</key>\n\t\t\t<string>$SSID</string>\n";
my $xml_HS20_a = '';

if ( $Passpoint ){
$xml_HS20_a = <<"EOS";
			<key>DisplayedOperatorName</key>
			<string>$friendlyName</string>
			<key>DomainName</key>
			<string>$HomeDomain</string>
EOS
	$xml_HS20 = '';
	$RCOI =~ s/\s*//g;
	if ( $RCOI ne '' ){
		$RCOI = uc $RCOI;
		my @ois = split(/,/, $RCOI);
		$xml_HS20 .= "\t\t\t<key>RoamingConsortiumOIs</key>\n";
		$xml_HS20 .= "\t\t\t<array>\n";
		for my $oi (@ois){
			$xml_HS20 .= "\t\t\t\t<string>$oi</string>\n";
		}
		$xml_HS20 .= "\t\t\t</array>\n";
	}

	if ( $NAIrealm ne '' ){
		$xml_HS20 .= "\t\t\t<key>NAIRealmNames</key>\n";
		$xml_HS20 .= "\t\t\t<array>\n";
		$xml_HS20 .= "\t\t\t\t<string>$NAIrealm</string>\n";
		$xml_HS20 .= "\t\t\t</array>\n";
	}
	$xml_HS20 .= "\t\t\t<key>ServiceProviderRoamingEnabled</key>\n\t\t\t<true/>\n";
}

my $xml_Expire = '';
if ( $ExpirationDate ne '' ){
$xml_Expire = <<"EOS";
	<key>RemovalDate</key>
	<date>$ExpirationDate</date>
EOS
}

my $xml_anchor = '';
my $xml_cert = '';
if ( $ICAfile ne '' ){
my $cert = '';
	open my $fh, '<', $ICAfile;
	while(<$fh>){
		if ( $_ =~ /BEGIN\s+CERTIFICATE/ ){ next; }
		if ( $_ =~ /END\s+CERTIFICATE/ ){ last; }
		$cert .= $_;
	}
	close $fh;
	chomp $cert;
	$cert =~ s/[\r\n]//g;

$xml_anchor = <<"EOS";
				<key>PayloadCertificateAnchorUUID</key>
				<array>
					<string>$uuid2</string>
				</array>
EOS

$xml_cert = <<"EOS";
		<dict>
			<key>PayloadDisplayName</key>
			<string>$ICAcertname</string>
			<key>PayloadType</key>
			<string>com.apple.security.pkcs1</string>
			<key>PayloadUUID</key>
			<string>$uuid2</string>
			<key>PayloadIdentifier</key>
			<string>com.apple.security.pkcs1.$uuid2</string>
			<key>PayloadVersion</key>
			<integer>1</integer>
			<key>PayloadContent</key>
			<data>
				$cert
			</data>
		</dict>
EOS
}

my $xmltext;
if ( $client_cert ){

$xmltext = <<"EOS";
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>PayloadDisplayName</key>
	<string>$PayloadDisplayName</string>
	<key>PayloadIdentifier</key>
	<string>$PLID</string>
	<key>PayloadRemovalDisallowed</key>
	<false/>
	<key>PayloadType</key>
	<string>Configuration</string>
	<key>PayloadUUID</key>
	<string>$PLuuid</string>
	<key>PayloadVersion</key>
	<integer>1</integer>
${xml_Expire}	<key>PayloadContent</key>
	<array>
		<dict>
			<key>AutoJoin</key>
			<true/>
			<key>CaptiveBypass</key>
			<false/>
			<key>DisableAssociationMACRandomization</key>
			<false/>
${xml_HS20_a}			<key>EAPClientConfiguration</key>
			<dict>
				<key>AcceptEAPTypes</key>
				<array>
					<integer>13</integer>
				</array>
				<key>TLSTrustedServerNames</key>
				<array>
					<string>$AAAFQDN</string>
				</array>
${xml_anchor}				<key>TTLSInnerAuthentication</key>
				<string>PAP</string>
				<key>TLSCertificateIsRequired</key>
				<true/>
				<key>TLSMaximumVersion</key>
				<string>1.2</string>
				<key>TLSMinimumVersion</key>
				<string>1.2</string>
			</dict>
			<key>EncryptionType</key>
			<string>WPA2</string>
			<key>HIDDEN_NETWORK</key>
			<false/>
			<key>IsHotspot</key>
			<false/>
			<key>PayloadCertificateUUID</key>
			<string>$cert_uuid</string>
			<key>PayloadDescription</key>
			<string>$description</string>
			<key>PayloadDisplayName</key>
			<string>Wi-Fi</string>
			<key>PayloadIdentifier</key>
			<string>com.apple.wifi.managed.$uuid1</string>
			<key>PayloadType</key>
			<string>com.apple.wifi.managed</string>
			<key>PayloadUUID</key>
			<string>$uuid1</string>
			<key>PayloadVersion</key>
			<integer>1</integer>
			<key>ProxyType</key>
			<string>None</string>
${xml_HS20}		</dict>
		<dict>
			<key>Password</key>
			<string>$client_cert_pass</string>
			<key>PayloadCertificateFileName</key>
			<string>${uname}.p12</string>
			<key>PayloadContent</key>
			<data>
$client_cert
			</data>
			<key>PayloadDescription</key>
			<string>Add certificate in PKCS#12 format.</string>
			<key>PayloadDisplayName</key>
			<string>${uname}.p12</string>
			<key>PayloadIdentifier</key>
			<string>com.apple.security.pkcs12.$cert_uuid</string>
			<key>PayloadType</key>
			<string>com.apple.security.pkcs12</string>
			<key>PayloadUUID</key>
			<string>$cert_uuid</string>
			<key>PayloadVersion</key>
			<integer>1</integer>
		</dict>
${xml_cert}	</array>
</dict>
</plist>
EOS

}
else{

$xmltext = <<"EOS";
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>PayloadDisplayName</key>
	<string>$PayloadDisplayName</string>
	<key>PayloadIdentifier</key>
	<string>$PLID</string>
	<key>PayloadRemovalDisallowed</key>
	<false/>
	<key>PayloadType</key>
	<string>Configuration</string>
	<key>PayloadUUID</key>
	<string>$PLuuid</string>
	<key>PayloadVersion</key>
	<integer>1</integer>
${xml_Expire}	<key>PayloadContent</key>
	<array>
		<dict>
			<key>AutoJoin</key>
			<true/>
			<key>CaptiveBypass</key>
			<false/>
			<key>DisableAssociationMACRandomization</key>
			<false/>
${xml_HS20_a}			<key>EAPClientConfiguration</key>
			<dict>
				<key>AcceptEAPTypes</key>
				<array>
					<integer>21</integer>
					<integer>25</integer>
				</array>
				<key>TLSMaximumVersion</key>
				<string>1.2</string>
				<key>TLSMinimumVersion</key>
				<string>1.2</string>
				<key>TLSTrustedServerNames</key>
				<array>
					<string>$AAAFQDN</string>
				</array>
${xml_anchor}				<key>TTLSInnerAuthentication</key>
				<string>PAP</string>
				<key>UserName</key>
				<string>$uname</string>
				<key>UserPassword</key>
				<string>$passwd</string>
				<key>OuterIdentity</key>
				<string>$anonID</string>
			</dict>
			<key>EncryptionType</key>
			<string>WPA2</string>
			<key>HIDDEN_NETWORK</key>
			<false/>
			<key>IsHotspot</key>
			<false/>
			<key>PayloadDescription</key>
			<string>$description</string>
			<key>PayloadDisplayName</key>
			<string>Wi-Fi</string>
			<key>PayloadIdentifier</key>
			<string>com.apple.wifi.managed.$uuid1</string>
			<key>PayloadType</key>
			<string>com.apple.wifi.managed</string>
			<key>PayloadUUID</key>
			<string>$uuid1</string>
			<key>PayloadVersion</key>
			<integer>1</integer>
			<key>ProxyType</key>
			<string>None</string>
${xml_HS20}		</dict>
${xml_cert}	</array>
</dict>
</plist>
EOS

}


print <<EOS;
Content-Type: application/x-apple-aspen-config
Content-Disposition: attachment; filename="$FileName.mobileconfig"

EOS

if ( $signercert eq '' ){
	print $xmltext;
}
else{
	my $fh;
	if ( $signerchain eq '' ){
		open($fh, "| openssl smime -sign -nodetach -signer $signercert -inkey $signerkey -outform der");
	}
	else{
		open($fh, "| openssl smime -sign -nodetach -certfile ../etc/chain.pem -signer $signercert -inkey $signerkey -outform der");
	}
	print $fh $xmltext;
	close($fh);
}

exit(0);
