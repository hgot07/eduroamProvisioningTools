#!/usr/bin/perl
#
# eduroam Provisioning Tools
#  Helper for Windows eduroam profile provisioning
# 
# Usage:
#  - Run Redis server.
#  - Put this script in a resricted directory where an access control
#    is effective by Basic Authentication, etc.
#  - Adjust the URL so that it points to your own main CGI script
#    (eduroam-win.config).
#  - Modify the way how to get the ID of the accessed user.
# Notes:
#  - This script will pass the user ID (REMOTE_USER, etc.) 
#    to the main script using a random key through Redis.
#  - See also the main script eduroam-win.config.
#
# 20220731 Hideaki Goto (Tohoku University and eduroam JP)
# 20230118 Hideaki Goto (Tohoku University and eduroam JP)
#	+ Script URI auto-setting
# 20230511 Hideaki Goto (Tohoku University and eduroam JP)
#	+ Fixed very rare key conflict in redis
#

use String::Random;
use Redis;

$confCGI = "ms-settings:wifi-provisioning?uri=https://$ENV{'HTTP_HOST'}$ENV{'REQUEST_URI'}";
$confCGI =~ s/user\/eduroamwin-helper.cgi/ext\/eduroam-win.config/;

$TTL = 60;

my $sr = String::Random->new();

my $redis = Redis->new(server => 'localhost:6379') or die;
$uid = $ENV{'REMOTE_USER'};

my $cnt = 10;
do {
	$key = $sr->randregex('[a-zA-Z0-9]{20}');
} while ( ! $redis->set($key, "$uid", 'EX', $TTL, 'NX') && $cnt-- >0 );

print << "EOS";
Content-Type: text/html

<head>
<meta http-equiv="refresh" content="0;URL=$confCGI?ukey=$key">
</head>
<body>
<ul>
<li> <a href="$confCGI?ukey=$key">Download Wi-Fi profile.</a> (within $TTL sec.)
</ul>
</body>
EOS

exit(0);
