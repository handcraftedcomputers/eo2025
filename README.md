# "I come to bury Ansible, not to praise it!"
## Everything Open 2025

My [pyinfra talk](https://2025.everythingopen.au/schedule/presentation/80/) and notes from
[Everything Open 2025](https://2025.everythingopen.au/).  I'll link the video once it's
been uploaded to EweToob (this is waiting on external parties).

This file is definitely Work In Progress.

##  Licence

<p xmlns:cc="http://creativecommons.org/ns#">Documents in this repository are licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC-SA 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/sa.svg?ref=chooser-v1" alt=""></a> :</p>

 - `eo2025.pdf`
 - `README.md`

Code files in this repository fall under the MIT Licence:

 - `inventory.py`
 - `update_lets_encrypt.py`
 - `utils.py`


##  To run

1.  Clone the repo.

1.  Get yourself some pyinfra.  This code was written against a freshly released 3.2 version
(10 days old at the time of the talk), but untested against earlier versions.  YMMV.

    ```
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv)$ pip3 install pyinfra==3.2
    ```

1.  Modify the inventory as required (paths to certificates, point to real servers, ssh keys
and sudo access).

1.  Run the sod.

    `(venv)$ pyinfra inventory.py update_lets_encrypt.py`

    Without the "-y" flag, 3.x pyinfra will prompt before applying operations.
Hit <return> if you dare, or power cycle the building to abort.

##  Bugs

-  Not entirely 100% idempotent.

    The `update_cert` method returns True if a certificate was successfully
updated, which is used to signal the `reload_svc` operation; if a deploy
aborts after the update but before the reload, then future runs won't update
the certificate (as it's already been done), and the service continues to
remain "unrestarted".

    I think/feel the workaround here would be to *also* check the uptime
of the service against the age of the certificates in question, but
closing that edge case would have complicated the example code.

-  The `reload_svc` operations reported during the run are sometimes named
incorrectly (most notably, "postfix" sometimes calls itself "lighttpd").
This is intermittent, and I'm unsure if this is a me thing or not (under
current investigation).  However this is only cosmetic; the reload itself
appears to be performed correctly.

##  Additional Notes

The slide show on its own probably requires the actual talk to make sense, especially
as it's peppered throughout with my "quirky" sense of self.  Due to running out of
time, I didn't get to explain in detail the upgrade process, or some of the nuances
of the code (especially around the "Big Oof" comments).

Some items in no particular order.

-  "Big Oof #1" - use of strings.

   While the inventory host data can be any form of Python data structure, we can
only pass strings via the command line, so we parse a comma separated list of
domain names here instead of using a list.

-  "Big Oof #2"

   This was more around a "programming in system teams" scenario.  While I have
no issues with list comprehensions, I am aware that there are those who do, so
if this was a team shared script I'd rewrite it to use a less idiomatic but
"plainer speakin'" code style.  Know, and code for, your audience.

-  One feature I really wanted to point out about pyinfra is that it's a library with
a CLI wrapper.  While we traditionally run the inventory/deploy scripts from the CLI,
ultimately I was to be run this from a higher level automation system, and I believe I
can introspect the run cleanly without having to eyeball parse the text output of a
utility that's likely to change.

-  I normally code deploys fairly explicitly for what is being changed;
e.g. the inventory would list the certificates per host, and the services
dependant on those certificates.  This deploy is a lot more "implicit driven" -
it updates certificates only if they already exist, and it's not an error if they
don't.  I'm actually comfortable with my lifestyle choice(s).

-  My archive technique consists of an "old\_certs" directory under the particular
certificates directory, and old certificates are moved into there after being
renamed to their sha1sum hash (to ensure they don't clobber over previous versions
of themselves).  Actual maintenance of the number of certs hasn't been implemented
(yet).

-  The method `concat_files` returns a Python StringIO (technically, a BytesIO)
object, which is an in memory file.  No temporary files to delete after a
(successful or otherwise) run.  We use this method to construct a certificate
that combines the key and full chain, which is what most web and mail servers
require.

-  `reload_svc` is also written more implicitly; we ask for a service to be
"reloaded", but don't know what type of service manager it runs under (not listed
here, but I also run daemontools elsewhere, from which runit was derived), so
this operation figures it out for us using facts.  I've had to special case
lighttpd's reload as it uses SIGUSR1 to perform a graceful restart, which runit's
reload doesn't use.  Not sure how I feel about the special casing at this stage
(normally not a fan, but post conference - meh).

Daryl Tester, 2025-01-24.
eo2025@handcraftedcomputers.com.au
