
from vanilla import VanillaApp, Transaction, Result
from vanilla.utils import home_dir, int_to_big_endian, big_endian_to_int

# Some simple 'helpers' for the app
DATA_KEY=b'current_count'
INITIAL_COUNT = int_to_big_endian(1)

def _increment_and_convert(bigint):
    v = big_endian_to_int(bigint)
    v += 1
    return int_to_big_endian(v)

# Setup the application. Pointing it to the same root dir used by Tendermint
# in this example, we are using ~/.vanilla, which means we set a different
# root_dir when running 'init':  'tendermint init --root ~/.vanilla'
app = VanillaApp(home_dir('.vanilla'))
app.debug = True

# Called only once on the first initialization of the application
# this is a good place to put stuff in state like default accounts, storage, etc...
@app.on_initialize()
def create_count(storage):
    storage.confirmed.put_data(DATA_KEY, INITIAL_COUNT)
    storage.state.save()

# Called per incoming tx (used in abci.check_tx).
# Put your transaction validation logic here.  Transaction passing this test
# are placed in the mempool.  If you don't specify this callback, all Tx pass
# by default
@app.validate_transaction()
def run_check_tx(tx, storage):
    stored_value = storage.unconfirmed.get_data(DATA_KEY)
    if tx.value != big_endian_to_int(stored_value):
        return Result.error(log="Don't match!")

    next_value = _increment_and_convert(stored_value)
    storage.unconfirmed.put_data(DATA_KEY, next_value)
    return Result.ok()

# Add more or more of these.  This is your apps business logic.
@app.on_transaction('counter')
def increment_the_count(tx, storage):
    stored_value = storage.confirmed.get_data(DATA_KEY)
    next_value = _increment_and_convert(stored_value)
    storage.confirmed.put_data(DATA_KEY,next_value)
    return Result.ok()

# Fire it up!
app.run()
