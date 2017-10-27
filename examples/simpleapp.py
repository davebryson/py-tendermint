
from tendermint import TendermintApp
from tendermint.utils import (
    home_dir,
    int_to_big_endian,
    big_endian_to_int
)

# Some simple 'helpers' for the app
DATA_KEY=b'current_count'
INITIAL_COUNT = int_to_big_endian(1)

# Setup the application. Pointing it to the same root dir used by Tendermint
# in this example, we are using ~/.vanilla, which means we set a different
# root_dir when running 'init':  'tendermint init --root ~/.vanilla'
app = TendermintApp(home_dir('.pytendermint'))
app.debug = True

# Called only once on the first initialization of the application
# this is a good place to put stuff in state like default accounts, storage, etc...
@app.on_initialize()
def create_count(storage):
    storage.confirmed.put_data(DATA_KEY, INITIAL_COUNT)

# Add more or more of these.  This is your apps business logic.
@app.on_transaction('counter')
def increment_the_count(tx, db):
    stored_value = db.get_data(DATA_KEY)
    v = big_endian_to_int(stored_value)
    v += 1
    db.put_data(DATA_KEY,int_to_big_endian(v))
    return True

# Calls to the path '/data' with a given key from the client
# will call this handler
@app.on_query('/data')
def handle_nonce(key, db):
    return db.get_data(key)

# Fire it up!
app.run()
