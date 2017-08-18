import rlp

from vanilla.accounts import Account
from vanilla.keys import Key

def test_account():
    bob = Key.generate()
    acct = Account.create_account(bob.publickey(tohex=True))

    assert(acct)
    assert(acct.nonce == 0)
    assert(acct.balance == 0)
    assert(bob.address() == acct.address())
    assert(bob.publickey() == acct.pubkey)

    serial = rlp.encode(acct, sedes=Account)
    acct_revived = rlp.decode(serial, sedes=Account)
    assert(acct_revived)
    assert(acct_revived.nonce == 0)
    assert(acct_revived.balance == 0)
    assert(bob.address() == acct_revived.address())
    assert(bob.publickey() == acct_revived.pubkey)

    acct_revived.allow_changes()
    acct_revived.nonce = 1
    assert(acct_revived.nonce == 1)
