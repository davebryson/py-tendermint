
protobuf:
	protoc -I=abci --python_out=abci vanilla/abci/types.proto

abci-test:
	sh ./compat-test.sh

rte:
	rm -Rf ~/.vanilla
	tendermint --home ~/.vanilla init

run-test-node:
	tendermint --home ~/.vanilla node

dev-mode:
	pip install --editable .
