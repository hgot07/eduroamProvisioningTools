# eduroamProvisioningTools
Tools and example codes for eduroam profile provisioning. (eduroam-OpenRoaming is not supported, but modification would be easy.)

Only EAP-TTLS is supported. If you want to use EAP-TLS, you need to write your own code. Some OSs may not support EAP-TLS.

## Features
- The tools and codes help institutions develop their own eduroam profile provisioning systems.
- The CGI scripts allow end users to download eduroam profile and configure the user device without typing in eduroam ID/password (or certificate). [geteduroam](https://www.geteduroam.app/) is a recommended app for device configuration.

## Directory layout
- user: Website with user's login, i.e., with an access control.
- ext: Open website where Windows Wi-Fi Settings can download the profile from.
- etc: Storage for configuration and certificate files. (Access restriction is necessary.)

## Requirements
Redis or compatible server is needed on the same host.

CGI scripts require execution handler,
 e.g. "AddHandler cgi-script .cgi .config" in case of Apache2 web server.

## About WPA2/WPA3 compatibility
These tools are compatible with WPA3. Even if you see WPA2 string in the profiles, it allows Apple and Microsoft devices to join WPA2 or WPA3 networks. 

Profile for Android (PPS MO) does not have such setting. You don't need to care.

## EAP-TLS support status
### Supported OS
These tools support EAP-TLS on the following operating systems.
- iOS/iPadOS
- macOS
- Some OSs supported by geteduroam

Unfortunately, Windows does not support EAP-TLS setting
 through the ms-settings: URI scheme as of Oct. 2024.
- cf. [Overview of Passpoint (Hotspot 2.0) in Windows](https://github.com/MicrosoftDocs/windows-driver-docs/blob/staging/windows-driver-docs-pr/mobilebroadband/passpoint.md)

A workaround is as follows, but this is cumbersome.
1. Operator issues a Passpoint profile for the EAP-TTLS method and
 a client certificate in PKCS #12 format.
1. User configures the device through the web-based provisioning
 and loads the client certificate manually.

### Note on Privacy Protection
EAP-TLS (RFC 5216) is not always so secure in terms of privacy.
When TLS 1.2 or older is used,
Access Network Providers can snoop into the contents of client certificates.
An efficient and straightforward solution would be
 to use TLS 1.3.

When TLS 1.3 is not available on user devices,
a compromised solution would be to use
"EAP-TTLS with EAP-TLS as inner method".
Client certificates are protected by the encrypted tunnel of EAP-TTLS.
Some supplicants like wpa_supplicant and Windows support this configuration,
 but the ms-settings: URI scheme does not work as explained above.

