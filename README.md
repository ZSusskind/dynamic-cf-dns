First, you'll need to change the "email" and "api\_key" fields to your Cloudflare email and api key.

Since your API key is present in plaintext, it's probably not a bad idea to restrict ownership and/or change ownership to root:
    sudo chown root:root update_dns.py
    sudo chmod 700 update_dns.py

Make a directory for the file; I put it under /usr/local/sbin:
    sudo mkdir /usr/local/sbin/update_dns
    sudo mv update_dns.py /usr/local/sbin/update_dns/.

Then you can set it to run as a cronjob:
    sudo crontab -e

Add entries to run after a reboot and however often you like (example runs every hour):
    @reboot         /usr/local/sbin/update_dns/update_dns.py
    0 * * * *       /usr/local/sbin/update_dns/update_dns.py

This is a pretty simple/hacky script in that it updates ALL the `A` and `AAAA` entries it finds. Should be easy enough to modify if you need something more advanced.
