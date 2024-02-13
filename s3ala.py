import click

@click.command()
@click.argument('bucket')
@click.argument('prefix')
@click.argument('start', type=click.DateTime())
@click.argument('end', type=click.DateTime())
def main(bucket, prefix, start, end):
    click.echo(bucket)
    click.echo(prefix)
    click.echo(start)
    click.echo(end)
