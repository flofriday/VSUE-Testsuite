#!/usr/bin/python3
from multiprocessing import Process
import socket
import time
import sys


# this line will intentionally crash so you remember to enter your port range
# e.g. 10080 if ports 10080-10089 have been assigned to you and configured in the application
port_range = 1xxxx0

mailbox_port = port_range + 4
transfer_port = port_range + 0
dmap_port = port_range + 5

# this stuff controls how intense the tests are
# if you want to challenge your servers, try to double or quadruple the "num_connections_per_trial"

num_connections_per_trial = (
    100  # must be a multiple of (num_users//3*2). don't ask
)
mails_per_connection = 10
num_users = 150  # must be divisible by 3. use the provided config file maybe. or not, idk
ultra_hardcore = False  # "who needs to read what comes back when we can just start a new socket right away?", they said


def send_nn_messages(dmtp_port, fr0m, to, subject="sub", data="d", log=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sr = s.makefile("r")
    sw = s.makefile("w")
    host = socket.gethostname()
    s.connect((host, dmtp_port))

    def send(cmd):
        if log:
            print(cmd)
        sw.write(cmd + "\n")

    for _ in range(mails_per_connection):
        send("begin")
        send("from " + fr0m)
        send("to " + to)
        send("subject " + subject)
        send("data " + data)
        send("send")
    send("quit")
    sw.flush()
    if not ultra_hardcore:
        sr.readlines()
    s.close()


def send_mailbox_mails():
    p1 = Process(target=send_mailbox_mails_part)
    p2 = Process(target=send_mailbox_mails_part)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def send_mailbox_mails_part():
    for i in range(num_connections_per_trial // 2):
        # the first 2 recipients are valid
        send_nn_messages(
            mailbox_port,
            "senderdoesntmatterhere@whatever.com",
            (
                f"{i % (num_users // 3)}@univer.ze,"
                f"{(i + 1) % (num_users // 3)}@univer.ze,"
                "idontexist@otherserver.com"
            ),
        )


def send_transfer_working():
    p1 = Process(target=send_transfer_working_part)
    p2 = Process(target=send_transfer_working_part)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def send_transfer_working_part():
    for i in range(num_connections_per_trial // 2):
        send_nn_messages(
            transfer_port,
            "zaphod@univer.ze",
            (
                f"{(num_users // 3) + i % (num_users // 3)}@univer.ze,"
                f"{(num_users // 3) + (i + 1) % (num_users // 3)}@univer.ze"
            ),
        )


def send_transfer_error():
    p1 = Process(target=send_transfer_error_part)
    p2 = Process(target=send_transfer_error_part)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def send_transfer_error_part():
    for i in range(num_connections_per_trial // 2):
        send_nn_messages(
            transfer_port,
            f"{num_users // 3 * 2 + i % (num_users // 3)}@univer.ze",
            "therecipientserver@doesnotexist.com",
        )


def check_state():
    print("Checking results.")
    print(
        "NOTE: If this gets stuck, there may not be enough emails for a user."
    )
    print()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sr = s.makefile("r")
    sw = s.makefile("w")
    host = socket.gethostname()
    s.connect((host, dmap_port))

    assert sr.readline().startswith("ok DMAP")

    def send(cmd):
        sw.write(cmd + "\n")
        sw.flush()

    for i in range(num_users):
        type = i // (num_users // 3)
        expected_emails = None
        if type <= 1:
            expected_emails = (
                num_connections_per_trial
                // (num_users // 3)
                * mails_per_connection
                * 2
            )
        else:
            expected_emails = (
                num_connections_per_trial
                // (num_users // 3)
                * mails_per_connection
            )

        send("login " + str(i) + " p")
        assert sr.readline().startswith("ok")
        print(
            f"Expecting user {i}/{num_users} to have {expected_emails} emails." 
        )
        send("list")
        send("logout")
        for j in range(expected_emails):
            line = sr.readline()
            if line.startswith("ok"):
                print(
                    f"Probably not enough emails for user {i}."
                    f"Only {j} out of {expected_emails} emails found."
                )
                if i < 50:
                    print(
                        "This user was tested by sending DMTP directly to the MailboxServer"
                    )
                elif i < 100:
                    print(
                        "This user was tested by sending DMTP through the TransferServer"
                    )
                else:
                    print(
                        "This user was tested by sending DMTP through the TransferServer and generating a error mail."
                    )

                exit(1337)

        if sr.readline().startswith("ok"):
            print(" - ok")
        else:
            print("There may be too many emails for user with id " + str(i))
            assert False

    send("quit")
    s.close()


if __name__ == "__main__":
    print(
        "Hi. Thanks for choosing this script 'n' stuff. You will probably regret it :)"
    )
    print("Now bombarding your servers with garbage emails!")

    t0 = time.time()
    p1 = Process(target=send_mailbox_mails)
    p2 = Process(target=send_transfer_working)
    p3 = Process(target=send_transfer_error)
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()

    if len(sys.argv) > 1 and sys.argv[1] == "--skip-wait":
        print("Skipping wait.")
    else:
        print("Done. Waiting a bit for things to settle down.")
        print("You can skip this with the flag --skip-wait")
        time.sleep(5)
        print("(trust me, your servers probably need it)")
        time.sleep(5)

    check_state()

    print("Total time taken:")
    print((time.time() - t0) * 1000, "ms")
