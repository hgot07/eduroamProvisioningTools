#!/usr/bin/perl

sub getuserinfo {
	my ($webuser) = @_;
	my %userinfo;

	if ( !defined $webuser ){
		$userinfo{'userID'} = '';
		return(%userinfo);
	}

# Write your own code here to set per-user parameters.

	$userinfo{'userID'} = 'name@example.com';
	$userinfo{'passwd'} = 'nicePassword';
	$userinfo{'ExpirationDate'} = '2023-01-05T00:00:00Z';


	# The scripts issue EAP-TLS profiles 
	#  when client_cert(_np) is non-empty.

	# Client Certificate for EAP-TLS (Android, etc.)
	# (Base64 enc., PKCS #12 containing client cert.&key, w/o passwd)
	$userinfo{'client_cert_np'} = '';

	# Client Certificate for EAP-TLS (macOS, etc.)
	# (Base64 enc., PKCS #12 containing client cert.&key, with passwd)
	$userinfo{'client_cert'} = '';
	$userinfo{'client_cert_pass'} = '';

	# SHA256 fingerprint of the Client Certificate
	$userinfo{'client_hash'} = '01:02:03:...';

	return(%userinfo);
}

1;
