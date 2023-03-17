"""The server for the relion job emailer."""
import asyncio
import configparser
import email.message
import json
import logging
import os.path
import traceback
import typing
from itertools import groupby
from operator import attrgetter

import aiosmtplib


config = configparser.ConfigParser()
config.read([
    "relion-emailer-server.conf",
    "/etc/relion-emailer-server.conf",
])


class Job(typing.NamedTuple):
    """A NamedTuple representing a finished job."""
    path: str
    nodename: str
    time: str

    @classmethod
    def from_dict(cls, job_dict):
        """Create a Job from a job dict."""
        return cls(**job_dict)

    @property
    def status(self):
        """Return the exit status of the job.

        One of "SUCCESS", "FAILURE", and "ABORTED".
        """
        return os.path.basename(self.path)[len("RELION_JOB_EXIT_"):]

    @property
    def job_number(self):
        """Return the job number of the job."""
        job_fname = os.path.basename(os.path.dirname(self.path))
        assert len(job_fname) == 6  # job001
        return int(job_fname[3:].lstrip("0"))


async def handle_message(reader, writer):
    data = await reader.read()
    logging.info("received message: %s", data)

    jobs_path = config["relion-emailer-server"]["jobs_path"]
    with open(jobs_path , "a") as f:
        f.write(str(data, "utf-8"))
        f.write("\n")


def parse_job(line):
    """Parse one job line and return a Job object."""
    return Job.from_dict(json.loads(line))


def pop_all_jobs():
    """Read all jobs from file and clear the file afterwards."""
    jobs_path = config["relion-emailer-server"]["jobs_path"]
    try:
        with open(jobs_path) as f:
            jobs = [parse_job(line) for line in f]
    except FileNotFoundError:
        return []

    with open(jobs_path, "w") as f:
        f.write("")

    return jobs


def build_message(jobs):
    """Builds an email.message.EmailMessage from a list of jobs.

    This looks up sender_email and recipients in the config.
    """
    # Sender email
    sender_email = config["relion-emailer-server"]["sender_email"]

    # Recipients
    recipients = [
        s.strip()
        for s in config["relion-emailer-server"]["recipients"].strip().split("\n")
    ]

    # Text content
    sorted_jobs = sorted(jobs, key=attrgetter("nodename", "time"))
    sections = []
    for nodename, node_jobs in groupby(sorted_jobs, key=attrgetter("nodename")):
        jobs_str = "\n".join(
            f"{job.job_number}: {job.status}: {os.path.dirname(job.path)}"
            for job in node_jobs
        )
        sections.append(f"{nodename}:\n{jobs_str}\n")

    text_content = "\n".join(sections)

    # Message creation
    message = email.message.EmailMessage()
    message["Subject"] = f"[relion-emailer] {len(jobs)} jobs finished"
    message["From"] = sender_email
    message["To"] = ",".join(recipients)
    message.set_content(text_content)

    return message


async def send_email():
    """Send the notification email if possible."""
    jobs = pop_all_jobs()

    if len(jobs) == 0:
        logging.info("no finished jobs, skipping sending...")
        return

    message = build_message(jobs)
    logging.info("send email: \n%s", str(message))
    await aiosmtplib.send(
        message,
        hostname=config["relion-emailer-server"]["smtp_host"],
        username=config["relion-emailer-server"]["sender_email"],
        password=config["relion-emailer-server"]["sender_password"],
        use_tls=True
    )


async def email_at_interval():
    interval_seconds = config["relion-emailer-server"].getint("email_interval_seconds")
    logging.info("started email at an interval of %d seconds", interval_seconds)
    while True:
        await asyncio.sleep(interval_seconds)
        logging.info("trying to send email")
        try:
            await send_email()
        except Exception as e:
            traceback.print_exc()
            raise e


async def main():
    server = await asyncio.start_server(
        handle_message,
        config["relion-emailer-server"]["host"],
        config["relion-emailer-server"]["port"]
    )

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'serving on {addrs}')

    task = asyncio.create_task(email_at_interval())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    asyncio.run(main())
