# eduroamProvisioningTools
Tools and example codes for eduroam profile provisioning. (eduroam-OpenRoaming is not supported, but modification would be easy.)

Only EAP-TTLS is supported. If you want to use EAP-TLS, you need to write your own code. Some OSs may not support EAP-TLS.

## Features
- The tools and codes help institutions develop their own eduroam profile provisioning systems.
- The CGI scripts allow end users to download eduroam profile and configure the user device without typing in eduroam ID/password (or certificate). [geteduroam](https://www.geteduroam.app/) is a recommended app for device configuration.

## Directory layout
- user: Website with user's login, i.e., with access control.
- ext: Open website where Windows Wi-Fi Settings can download the profile from.
- etc: Storage for configuration and certificate files.

## About WPA2/WPA3 compatibility
The tools are compatible with WPA3. Even if you see WPA2 string in the profiles, it allows Apple and Microsoft devices to join WPA2 or WPA3 networks. Profile for Android (PPS MO) does not have such setting.
