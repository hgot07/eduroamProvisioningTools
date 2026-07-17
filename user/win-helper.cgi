#!/usr/bin/perl
#
# Wi-Fi Provisioning Tools
#  Helper for Windows Wi-Fi provisioning
# 
# 20260715 Hideaki Goto (Tohoku University and eduroam JP)
#       Modernize.
# 20260717 Hideaki Goto (Tohoku University and eduroam JP)
#	Ease configuration. Some fixes and feature extentions.
#

use strict;
use warnings;
#use CGI;
use CGI::Cookie;
use Digest::SHA qw(hmac_sha256 hmac_sha256_base64);
use MIME::Base64;
use MIME::Base64::URLSafe;
use Crypt::CBC;
use Crypt::Cipher::AES;
use Config::Tiny;

#require '../etc/check-login.pl';

my $time = time();

my $webuser = $ENV{'REMOTE_USER'};
if ( !defined $webuser ){ exit(1); }

#my $q = CGI->new();


my $config = Config::Tiny->read('../etc/config.ini');
if ( ! defined $config ){
print <<EOS;
Content-Type: text/plain; charset=utf-8

No configuration file found.
EOS
	exit(0);
}

my $ukey_pass = $config->{default}->{HelperSecret};

my $cipher = Crypt::CBC->new(
	-key	=> $ukey_pass,
	-cipher	=> 'Cipher::AES',
	-pbkdf	=> 'pbkdf2',
);

my $sig = hmac_sha256_base64($webuser, $ukey_pass);
my $ukey = urlsafe_b64encode( $cipher->encrypt( $webuser.":".$sig ) );

my $URI = $ENV{'REQUEST_URI'};
$URI =~ s/\?.*//;
my $confCGI = "ms-settings:wifi-provisioning?uri=https://$ENV{'HTTP_HOST'}$URI";
$confCGI =~ s/user\/win-helper.cgi/ext\/wifi-win.cgi/;

print << "EOS";
Content-Type: text/html

<html>
<head>
<meta http-equiv="refresh" content="0;URL=$confCGI?ukey=$ukey">
</head>
<body>
<- <a href=".">back</a>
</body>
</html>
EOS

exit(0);
