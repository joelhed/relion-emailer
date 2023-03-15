"""The server for the relion job emailer."""
import asyncio
import json


EMAIL_INTERVAL_SECONDS = 30 # 60 * 15
JOBS_FILENAME = "jobs.jsonl"

async def handle_message(reader, writer):
    data = await reader.read()
    print("received message: ", data)

    with open(JOBS_FILENAME, "a") as f:
        f.write(str(data, "utf-8"))
        f.write("\n")


def parse_job(line):
    return json.loads(line)


def pop_all_jobs():
    """Read all jobs from file and clear the file afterwards."""
    with open(JOBS_FILENAME) as f:
        jobs = [parse_job(line) for line in f]

    with open(JOBS_FILENAME, "w") as f:
        f.write("")

    return jobs


async def send_email():
    """ """
    jobs = pop_all_jobs()
    print("send email with jobs:")
    for job in jobs:
        print(job)


async def email_at_interval():
    print("started email at interval")
    while True:
        await asyncio.sleep(EMAIL_INTERVAL_SECONDS)
        print(EMAIL_INTERVAL_SECONDS, "seconds has passed")
        await send_email()


async def main():
    server = await asyncio.start_server(handle_message, "0.0.0.0", 62457)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    task = asyncio.create_task(email_at_interval())

    async with server:
        await server.serve_forever()


asyncio.run(main())
