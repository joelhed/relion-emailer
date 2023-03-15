#!/usr/bin/env python3
"""The client for the relion emailer.

This watches the node for any finished jobs and notices the server when that happens.
"""
import datetime
import json
import logging
import os.path
import socket
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class RelionJobExitedEventHandler(FileSystemEventHandler):

    def on_created(self, event):
        name = os.path.basename(event.src_path)
        if not name.startswith("RELION_JOB_EXIT"):
            return

        message = create_message(event.src_path)
        notify_server(message)


def create_message(src_path):
    """Create a bytes message to the server from the path of a RELION_JOB_EXITED_* file."""
    json_str = json.dumps({
        "status": os.path.basename(src_path)[len("RELION_JOB_EXIT_"):],
        "nodename": socket.gethostname(),
        "path": os.path.dirname(src_path),
        "time": datetime.datetime.now().isoformat(),
    })
    return bytes(json_str, "utf-8")


def notify_server(message):
    """Send the passed message to the server."""
    logging.info("sending message: %s", str(message))
    with socket.create_connection(("localhost", 62457)) as s:
        s.sendall(message)


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = RelionJobExitedEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while observer.isAlive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
