reset:
	rm -Rf ~/.pyvanilla
	tendermint --home ~/.pyvanilla init

run-test-node:
	tendermint --home ~/.pyvanilla node

dev-mode:
	pip install --editable .
