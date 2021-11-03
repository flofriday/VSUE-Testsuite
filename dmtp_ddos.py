#!/usr/bin/python3
from multiprocessing import Process
import socket
import time


# this line will intentionally crash so you remember to enter your port range
# e.g. 10080 if ports 10080-10089 have been assigned to you and configured in the application
port_range = 10840

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

    for i in range(mails_per_connection):
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
    def process_half():
        for i in range(num_connections_per_trial // 2):
            # the first 2 recipients are valid
            send_nn_messages(
                mailbox_port,
                "senderdoesntmatterhere@whatever",
                (
                    str(i % (num_users // 3))
                    + "@univer.ze,"
                    + str((i + 1) % (num_users // 3))
                    + "@univer.ze,"
                    "idontexist@otherserver"
                ),
            )

    p1 = Process(target=process_half)
    p2 = Process(target=process_half)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def send_transfer_working():
    def process_half():
        for i in range(num_connections_per_trial // 2):
            send_nn_messages(
                transfer_port,
                "zaphod@univer.ze",
                (
                    str((num_users // 3) + i % (num_users // 3))
                    + "@univer.ze,"
                    + str((num_users // 3) + (i + 1) % (num_users // 3))
                    + "@univer.ze"
                ),
            )

    p1 = Process(target=process_half)
    p2 = Process(target=process_half)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


def send_transfer_error():
    def process_half():
        for i in range(num_connections_per_trial // 2):
            send_nn_messages(
                transfer_port,
                str(num_users // 3 * 2 + i % (num_users // 3)) + "@univer.ze",
                "therecipientserver@doesnotexist",
            )

    p1 = Process(target=process_half)
    p2 = Process(target=process_half)
    p1.start()
    p2.start()
    p1.join()
    p2.join()


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

    assert "ok DMAP" in sr.readline()

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
        assert "ok" in sr.readline()
        print(
            "Expecting user "
            + str(i)
            + "/"
            + str(num_users)
            + " to have "
            + str(expected_emails)
            + " emails."
        )
        send("list")
        send("logout")
        for j in range(expected_emails):
            line = sr.readline()
            if "ok" in line:
                print(
                    "Probably not enough emails for user "
                    + str(i)
                    + ". Only "
                    + str(j)
                    + " out of "
                    + str(expected_emails)
                    + " emails found."
                )
                exit(1337)

        if "ok" in sr.readline():
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

    print("Done. Waiting a bit for things to settle down.")
    time.sleep(5)
    print("(trust me, your servers probably need it)")
    time.sleep(5)

    check_state()

    print("Total time taken:")
    print((time.time() - t0) * 1000, "ms")
