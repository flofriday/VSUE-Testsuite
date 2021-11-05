# VSUE Testsuite

Originally these tests were written in 2019 by a user on mattermost.fsinf.at
called "superdau". I fixed some bugs, added a detailed (english) description
and published them on GitHub.

## Features

This script will send thousands of mails to the system and then after a short
pause count if all mails were received successfully. The mails are a mix of
direct mails to the mailserver, mails to the transferserver and errormails.

If you have race-conditions in your code, this script is likely to trigger them.
However, since race-conditions are not deterministic, there can never be a
guarantee.

These tests do not check if the monitoring server behaves correctly.

## How to use

1. Copy `users-univer-ze.properties` from this repo into the resource's folder.
2. Start `transfer-1` and `mailbox-univer-ze`.
3. Replace the port in the script.
4. Start the script with `python3 dmpt_ddos.py`

## Oh no my tests failed 😰

Don't panic.
So here is what you can learn from which tests failed.

- User 0-49 mails are sent directly to the mailbox-server (40 per user)
- User 50-99 mails are sent through the transfer-server (40 per user)
- User 100-149 mails are error-mails sent by the transfer-server (20 per user)

So if you get an error at User 100, it is likely that you only messed up the
error delivery.
