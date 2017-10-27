
import click
from tendermint import Transaction
from tendermint.client import RpcClient
from tendermint.utils import from_hex

rpc = RpcClient()

@click.group()
def cli():
    pass

@cli.command()
def check_status():
    """Check Tendermint status"""
    print(rpc.status())

@cli.command()
@click.argument('value')
def send_count(value):
    # TODO: These need to be signed with the proper tx
    t = Transaction()
    t.call = 'counter'
    t.value = int(value)
    raw = t.encode()

    result = rpc.send_tx_commit(raw)
    print(result)

@cli.command()
def view_count():
    result = rpc.query('/data','current_count')
    print(result['response']['value'])

if __name__ == '__main__':
    cli()
