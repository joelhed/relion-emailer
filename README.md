# relion-emailer

This program sends email notifications when your Relion jobs finish.

It is built with clusters in mind, with `relion-emailer-watcher` running on every node where Relion is running, and a `relion-emailer-server` on the head node.

## Installation

This requires python 3.8+ compiled with SSL on the server, and python 3.8+ with watchdog installed on the watchers.

To build the application archives, run `make`.
The resulting `*.pyz` files can be executed as is on your target machines.
Just make sure to install watchdog on your watcher nodes:

```
$ pip install watchdog==2.3.1
```

TODO: Installation instructions

