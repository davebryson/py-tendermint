import os.path

import pytest
import rlp
from vanilla.keys import Key
from vanilla.accounts import Account
from vanilla.state import State, StateCache, Storage
from vanilla.utils import home_dir

def test_state_storage():
    st,_ = State.load_state('')
    r1 = st.storage.root_hash

    # Values must be bytes
    with pytest.raises(TypeError):
        st.put_storage('dave','dave')

    # Must be a key
    with pytest.raises(TypeError):
        st.put_storage('','dave')


    st.put_storage('dave', b'dave')
    assert(r1 != st.storage.root_hash)
    assert(b'dave' == st.get_storage('dave'))

    assert(b'' == st.get_storage('doesnotexist'))

def test_state_account():
    bob = Key.generate()
    acct = Account.create_account(bob.publickey(tohex=True))
    st,_ = State.load_state('')
    r1 = st.storage.root_hash

    st.update_account(acct)
    r2 = st.storage.root_hash
    assert(r1 != r2)
    a = st.get_account(bob.address())

    assert(a)
    assert(a.pubkey == bob.publickey())

    st.update_account(None)
    assert(r2 == st.storage.root_hash)

    #st.increment_nonce(bob.address())
    #st.increment_nonce(bob.address())
    #st.increment_nonce(bob.address())
    #assert(r2 != st.storage.root_hash)
    #c = st.get_account(bob.address())
    #assert(c.nonce == 3)

def test_order_doesnt_matter():
    st1,_ = State.load_state('')
    st1.put_storage('a', rlp.encode(1))
    st1.put_storage('b', rlp.encode(2))
    st1.put_storage('c', rlp.encode(3))
    r1 = st1.storage.root_hash

    st2,_ = State.load_state('')
    st2.put_storage('b', rlp.encode(2))
    st2.put_storage('a', rlp.encode(1))
    st2.put_storage('c', rlp.encode(3))
    r2 = st2.storage.root_hash

    assert(r1 == r2)

def test_cache():
    bob = Key.generate()
    acct = Account.create_account(bob.publickey(tohex=True))

    dbfile = home_dir('temp', 'test.db')
    state,_ = State.load_state(dbfile)
    state.chain_id = 'testchain1'
    cache = StateCache(state)
    h1 = cache.commit()

    cache.update_account(acct)
    a = cache.get_account(bob.address())
    assert(a.address() == bob.address())

    cache.put_data(b'a', b'one')
    assert(b'one' == cache.get_data(b'a'))
    cache.put_data(b'a', b'two')
    assert(b'two' == cache.get_data(b'a'))

    cache.increment_nonce(bob.address())
    cache.increment_nonce(bob.address())
    cache.increment_nonce(bob.address())
    cache.increment_nonce(bob.address())
    b = cache.get_account(bob.address())
    assert(4 == b.nonce)

    state.last_block_height = 1
    cache.commit()
    h2 = state.save()
    assert(h1 != h2)
    state.close()

    # Reload from state and make sure all data is the same
    state2,_ = State.load_state(dbfile)
    assert(b'testchain1' == state2.chain_id)
    assert(1 == state2.last_block_height)
    # Should match our last apphash
    assert(h2 == state2.storage.root_hash)

    bobs = state2.get_account(bob.address())
    assert(4 == bobs.nonce)
    state2.close()

    if os.path.exists(dbfile):
        os.remove(dbfile)
        
def test_storage():
    alice = Key.generate()
    bob = Key.generate()
    acct = Account.create_account(bob.publickey(tohex=True))

    dbfile = home_dir('temp', 'test.db')
    state,_ = State.load_state(dbfile)
    state.chain_id = 'testchain1'
    storage = Storage(state)

    h1 = storage.commit()

    # Note: Haven't added bob to storage!
    storage.unconfirmed.increment_nonce(bob.address())
    bobs = storage.unconfirmed.get_account(bob.address())
    assert(b'' == bobs)

    storage.unconfirmed.update_account(acct)
    storage.unconfirmed.increment_nonce(bob.address())
    storage.unconfirmed.increment_nonce(bob.address())
    bobs = storage.unconfirmed.get_account(bob.address())
    assert(2 == bobs.nonce)

    alice_acct = Account.create_account(alice.publickey(tohex=True))
    storage.confirmed.update_account(alice_acct)
    storage.confirmed.increment_nonce(alice.address())
    alices = storage.confirmed.get_account(alice.address())
    assert(1 == alices.nonce)
    h2 = storage.commit()
    assert(h1 != h2)

    state2,_ = State.load_state(dbfile)
    storage2 = Storage(state2)
    alices = storage2.unconfirmed.get_account(alice.address())
    assert(1 == alices.nonce)
    bobs = storage2.unconfirmed.get_account(bob.address())
    assert(b'' == bobs)

    if os.path.exists(dbfile):
        os.remove(dbfile)
