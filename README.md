# py-Tendermint

**A Python microframework for building blockchain applications with Tendermint**

Inspired by Flask and the recent work on Tendermint's Quark SDK, Vanilla makes
it easy to quickly prototype a Tendermint ABCI application.

**NOTE:** *this is still very alpha stuff* DO NOT USE IN PRODUCTION.

Here's what a simple *stateful* counter app might look like:

py-tendermint hides some of the repetitive setup for you by providing:
* A Patricia Trie backed by persistent storage
* Common Transaction model based on RLP
* RPC Client
* Accounts
* ed25519 Keys

If you want to stay closer to the metal, check out the Tendermint Python ABCI library:
https://github.com/davebryson/py-abci


### Requirements
 * Python 3.6.x
 * Tendermint engine (of course)

 ### Install
 * `python setup.py install` (pip install in the future)

### Try it out
  * Run Tendermint 'init':  `tendermint --home ~/.vanilla init`  Note we use a different home directory.
  to keep all our blockchain apps seperate
  * In another terminal, start the Vanilla app: `python examples/hellovanilla.py`
  * Now start tendermint: `tendermint --home ~/.vanilla node`
  * Finally, open another terminal and talk to the app: `python examples/hellovanilla_client.py`
