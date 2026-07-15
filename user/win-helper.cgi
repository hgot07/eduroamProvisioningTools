#!/usr/bin/perl
#
# eduroam Provisioning Tools
#  Helper for Windows eduroam profile provisioning
# 

use strict;
use warnings;
use CGI::Cookie;
use Digest::SHA qw(hmac_sha256 hmac_sha256_base64);
use MIME::Base64;
use MIME::Base64::URLSafe;
use Crypt::CBC;
use Crypt::Cipher::AES;

#require '../etc/check-login.pl';

my $time = time();

my $webuser = $ENV{'REMOTE_USER'};
if ( !defined $webuser ){ exit(1); }


# CHANGE ME
my $ukey_pass = '4BQkGpgtc217OleZt7Gs9rSaVz7H0yDy';

my $cipher = Crypt::CBC->new(
	-key	=> $ukey_pass,
	-cipher	=> 'Cipher::AES',
	-pbkdf	=> 'pbkdf2',
);

my $sig = hmac_sha256_base64($webuser, $ukey_pass);
my $ukey = urlsafe_b64encode( $cipher->encrypt( $webuser.":".$sig ) );

my $confCGI = "ms-settings:wifi-provisioning?uri=https://$ENV{'HTTP_HOST'}$ENV{'REQUEST_URI'}";
$confCGI =~ s/user\/win-helper.cgi/ext\/eduroam-win.cgi/;

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
