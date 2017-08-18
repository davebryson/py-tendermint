
protobuf:
	protoc -I=abci --python_out=abci vanilla/abci/types.proto

test:
	sh ./compat-test.sh

reset-test:
	rm -Rf ~/.vanilla
	tendermint --home ~/.vanilla init
