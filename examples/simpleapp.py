
from tendermint import TendermintApp
from tendermint.utils import (
    home_dir,
    int_to_big_endian,
    big_endian_to_int
)

# Some constants for the app
DATA_KEY=b'current_count'
INITIAL_COUNT = int_to_big_endian(1)

# Setup the application. Pointing it to the same root dir used by Tendermint.
# In this example, we are using ~/.pytendermint, which means we set a different
# root_dir when running 'init':  'tendermint init --home ~/.pytendermint'
app = TendermintApp(home_dir('.pytendermint'))
app.debug = True

# Called only once on the first initialization of the application
# this is a good place to put stuff in state like default accounts, storage, etc...
@app.on_initialize()
def create_count(storage):
    storage.confirmed.put_data(DATA_KEY, INITIAL_COUNT)

# Add more or more of these.  This is your business logic to change state.
# In this example, Txs with a 'call' of 'counter' will increment the count
# in state.
@app.on_transaction('counter')
def increment_the_count(tx, db):
    stored_value = db.get_data(DATA_KEY)
    v = big_endian_to_int(stored_value)
    v += 1
    db.put_data(DATA_KEY,int_to_big_endian(v))
    return True

# Queries to state.  Add 1 or more of these.
# In this example, the a call to the path '/data' with a given key
# from the client will call this handler
@app.on_query('/data')
def handle_nonce(key, db):
    return db.get_data(key)

# Fire it up - it'll connect to Tendermint
app.run()
