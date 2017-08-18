
import click
from vanilla import Transaction
from vanilla.client import RpcClient

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
    t = Transaction()
    t.call = 'counter'
    t.value = int(value)
    raw = t.encode()

    result = rpc.send_tx_commit(raw)
    print(result)

@cli.command()
def view_count():
    result = rpc.query('nonce','')
    print(result['response']['value'])

if __name__ == '__main__':
    cli()
