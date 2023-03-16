#!/usr/bin/env python3
"""The client for the relion emailer.

This watches the node for any finished jobs and notices the server when that happens.
"""
import configparser
import datetime
import json
import logging
import os.path
import socket
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


config = configparser.ConfigParser()
config.read([
    "relion-emailer-watcher.conf",
    "/etc/relion-emailer-watcher.conf",
])


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
        "nodename": socket.gethostname(),
        "path": src_path,
        "time": datetime.datetime.now().isoformat(),
    })
    return bytes(json_str, "utf-8")


def notify_server(message):
    """Send the passed message to the server."""
    host_port = (
        config["relion-emailer-watcher"]["server_host"],
        config["relion-emailer-watcher"].getint("server_port")
    )
    logging.info("sending message to %s: %s", host_port, str(message))
    with socket.create_connection(host_port) as s:
        s.sendall(message)


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    watch_dir = config["relion-emailer-watcher"]["watch_dir"]
    event_handler = RelionJobExitedEventHandler()
    observer = Observer()
    observer.schedule(
        event_handler,
        watch_dir,
        recursive=True
    )
    logging.info("starting to watch %s", watch_dir)
    observer.start()
    try:
        while observer.isAlive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
