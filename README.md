# CRLSet-Mirror
Pulls down and installs CRLSet component for ungoogled-chromium users who want certificate revocation

Note that this does pull the latest CRLSet file directly from google. Not a terribly exciting bit of traffic since its basically 2 get requests to get the version and pull down the file, but its worth noting since this is for ungoogled chromium users. 

# Usage

### Install once without auto update
0. Locate your ungoogled chromium CertificateRevocation folder location.
1. Go to the releases tab and download the [mirror-crl artifact](https://github.com/tired-runner/CRLSet-Mirror/releases/download/latest/mirror-crl)
2. Make it executable with `chmod u+x mirror-crl`
3. Run it with `./mirror-crl --path <your CertificateRevocation location>`
4. Open ungoogled-chromium and navigate to [https://revoked.badssl.com/](https://revoked.badssl.com/). You should see an error from the revoked certificate!

### Set up auto updates with systemd
You could additionally created a timer file, or use whatever other mechanism systemd provides to schedule this however frequently you want. For this example, I am just using updating once on startup, which works for me because I turn off my computer at the end of the day. If you are putting it on a timer once every couple of hours would also be reasonable, and roughly match chrome's behavior.

0. Locate your ungoogled chromium CertificateRevocation folder location.
1. Go to the releases tab and download the [mirror-crl artifact](https://github.com/tired-runner/CRLSet-Mirror/releases/download/latest/mirror-crl)
2. Move it to where you want to keep it, for the purposes of these instructions will use ~/CRLUpdater
3. Make it executable with `chmod u+x mirror-crl`
4. navigate to the `~/.config/systemd/user` directory or create it if it does not exist
5. Run `touch mirror-crl.service` and then edit it with your text editor of choice
6.
   ```
   [Unit]
   Description=Update CRL list in ungoogled chromium
   After=network.service

   [Service]
   Type=oneshot
   ExecStart=<your home path>/CRLData/mirror-crl --path <your CertificateRevocation location>

   [Install]
   WantedBy=default.target
   ```
8. Run `systemctl --user enable mirror-crl.service`
9. reboot, and confirm with `systemctl --user status mirror-crl` that the crl updated successfully
10. Open ungoogled-chromium and navigate to [https://revoked.badssl.com/](https://revoked.badssl.com/). You should see an error from the revoked certificate!

### Non systemd auto updates
0. Locate your ungoogled chromium CertificateRevocation folder location.
1. Use chron or whatever other task scheduling mechanism to run `mirror-crl --path <your CertificateRevocation location>` with whatever frequency you want

### Locating your CertificateRevocation folder
This is a folder's location is platform dependent, places to look include
* `~/.config/chromium/CertificateRevocation`
* `~/.var/app/io.github.ungoogled_software.ungoogled_chromium/config/chromium/CertificateRevocation` This is where it is for me, since I am using a flatpak installation
