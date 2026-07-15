#!/usr/bin/perl
#
# eduroam Provisioning Tools
#  Simple CGI script for eduroam profile provisioning
#  Target: All OS
# 
# Usage:
#  - Customize the configuration part below and the external file
#    etc/eduroam-common.cfg.
#  - Put this script on a web server as a CGI program.
#    (Please refer to the HTTP server's manual for configuring CGI.)
#  - Access https://<path_to_script>/eduroam.eap-config.cgi.
# Notes:
#  -
# References:
#  - geteduroam
#    https://www.geteduroam.app/
#  - eduroam CAT
#    https://cat.eduroam.org/
#  - eap-metadata.xsd
#    https://github.com/GEANT/CAT/blob/master/devices/eap_config/eap-metadata.xsd
#
# 20220814 Hideaki Goto (Tohoku University and eduroam JP)
# 20220815 Hideaki Goto (Tohoku University and eduroam JP)
# 20220826 Hideaki Goto (Tohoku University and eduroam JP)
#	+ per-user ExpirationDate
# 20241030 Hideaki Goto (Tohoku University and eduroam JP)
#	Update a reference. Add EAP-TLS support.
# 20260620 Hideaki Goto (Tohoku University and eduroam JP)
#	Drop legacy workaround using <Username>
# 20260715 Hideaki Goto (Tohoku University and eduroam JP)
#	Modernize.
#

use strict;
use warnings;
use CGI::Cookie;
use DateTime;
use Digest::SHA qw(hmac_sha256 hmac_sha256_base64);
use MIME::Base64;
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

my $SSID = $config->{default}->{SSID};
my $AAAFQDN = $config->{default}->{AAAFQDN};
my $CAfile = $config->{default}->{CAfile};
my $cert = $config->{default}->{cert};
my $HomeDomain = $config->{default}->{HomeDomain};
my $friendlyName = $config->{default}->{friendlyName};

my %userinfo = getuserinfo($webuser);
my $userID = $userinfo{'userID'};
if ( $userID eq '' ){ exit(1); }

my $passwd = $userinfo{'passwd'};
my $ExpirationDate = $userinfo{'ExpirationDate'};
my $client_cert_np = $userinfo{'client_cert_np'};


my $uname = $userID;
my $anonID = $userID;
$anonID =~ s/^.*@/anonymous@/;

# EAP-TTLS with PAP
my $EAPMethods = <<"EOS";
        <EAPMethod>
          <Type>21</Type>
        </EAPMethod>
EOS
my $InnerAuth = <<"EOS";
        <InnerAuthenticationMethod>
          <NonEAPAuthMethod>
            <Type>1</Type>
          </NonEAPAuthMethod>
        </InnerAuthenticationMethod>
EOS

=pod
# PEAP
my $EAPMethods = <<"EOS";
        <EAPMethod>
          <Type>25</Type>
        </EAPMethod>
EOS
my $InnerAuth = <<"EOS";
        <InnerAuthenticationMethod>
          <EAPMethod>
            <Type>26</Type>
          </EAPMethod>
        </InnerAuthenticationMethod>
EOS
=cut

# EAP-TLS
if ( $client_cert_np ){
my $EAPMethods = <<"EOS";
        <EAPMethod>
          <Type>13</Type>
        </EAPMethod>
EOS
$InnerAuth = '';
}


#---- Profile composition part ----
# (no need to edit below, hopefully)

# Fix certificate format
chomp($client_cert_np);

my $ts=DateTime->now->datetime."Z";

my $xml_Expire = '';
if ( $ExpirationDate ne '' ){
	$xml_Expire = "    <ValidUntil>$ExpirationDate</ValidUntil>\n";
}

my $RCOI =~ s/\s*//g;
my $xml_RCOI = '';
if ( $RCOI ne '' ){
	my @ois = split(/,/, $RCOI);
	for my $oi (@ois){
		$xml_RCOI .= "      <IEEE80211>\n";
		$xml_RCOI .= "        <ConsortiumOID>$oi</ConsortiumOID>\n";
		$xml_RCOI .= "      </IEEE80211>\n";
	}
}

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
}


my $xml;
if ( $client_cert_np ){

$xml = <<"EOS";
<?xml version="1.0" encoding="utf-8"?>
<EAPIdentityProviderList xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="eap-metadata.xsd">
  <EAPIdentityProvider ID="$HomeDomain" namespace="urn:RFC4282:realm" lang="en" version="1">
${xml_Expire}    <AuthenticationMethods>
      <AuthenticationMethod>
${EAPMethods}        <ServerSideCredential>
          <CA format="X.509" encoding="base64">
$cert
          </CA>
          <ServerID>$AAAFQDN</ServerID>
        </ServerSideCredential>
        <ClientSideCredential>
          <OuterIdentity>$anonID</OuterIdentity>
          <ClientCertificate>$client_cert_np</ClientCertificate>
        </ClientSideCredential>
${InnerAuth}      </AuthenticationMethod>
    </AuthenticationMethods>
    <CredentialApplicability>
${xml_RCOI}    </CredentialApplicability>
    <ProviderInfo>
      <DisplayName>$friendlyName</DisplayName>
      <Helpdesk/>
    </ProviderInfo>
  </EAPIdentityProvider>
</EAPIdentityProviderList>
EOS

}
else {

$xml = <<"EOS";
<?xml version="1.0" encoding="utf-8"?>
<EAPIdentityProviderList xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="eap-metadata.xsd">
  <EAPIdentityProvider ID="$HomeDomain" namespace="urn:RFC4282:realm" lang="en" version="1">
${xml_Expire}    <AuthenticationMethods>
      <AuthenticationMethod>
${EAPMethods}        <ServerSideCredential>
          <CA format="X.509" encoding="base64">
$cert
          </CA>
          <ServerID>$AAAFQDN</ServerID>
        </ServerSideCredential>
        <ClientSideCredential>
          <OuterIdentity>$anonID</OuterIdentity>
          <UserName>$userID</UserName>
          <Password>$passwd</Password>
        </ClientSideCredential>
${InnerAuth}      </AuthenticationMethod>
    </AuthenticationMethods>
    <CredentialApplicability>
      <IEEE80211>
        <SSID>$SSID</SSID>
        <MinRSNProto>CCMP</MinRSNProto>
      </IEEE80211>
${xml_RCOI}    </CredentialApplicability>
    <ProviderInfo>
      <DisplayName>$friendlyName</DisplayName>
      <Helpdesk/>
    </ProviderInfo>
  </EAPIdentityProvider>
</EAPIdentityProviderList>
EOS

}

chomp $xml;

print <<"EOS";
Content-Type: application/eap-config
Content-Disposition: attachment; filename="eduroam.eap-config"

$xml
EOS

exit(0);


