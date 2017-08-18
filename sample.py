
from vanilla.utils import home_dir
from vanilla import VanillaApp, Transaction, Result


# Setup the application. Pointing it to the same root dir used by Tendermint
# in this example, we are using ~/.vanilla, which means we set a different
# root_dir when running 'init'.  'tendermint init --root ~/.vanilla'
app = VanillaApp(home_dir('.vanilla'))

# Called only once, on the first initialization of the application
# this is a good place to put stuff in state like default accounts, etc...
@app.on_initialize()
def create_default_accounts(storage):
    pass

# Called per incoming tx (used in abci.check_tx).  Will validate Tx based
# on logic
@app.validate_transaction()
def check_tx(tx, storage):
    pass


@app.process_transaction('create')
def create_one(tx, storage):
    pass


@app.querystate('nonce')
def get_nonce(params, storage):
    pass


if __name__ == '__main__':
    app.run()
