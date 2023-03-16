.PHONY: all

all: relion-emailer-server.pyz relion-emailer-watcher.pyz

relion-emailer-server.pyz: FORCE
	pip install -r server/requirements.txt --target server
	rm -rf server/*.dist-info
	python -m zipapp -p "/usr/bin/env python3" -o '$@' server

relion-emailer-watcher.pyz: FORCE
	python -m zipapp -p "/usr/bin/env python3" -o '$@' watcher

FORCE:
