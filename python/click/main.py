import click

@click.group()
def main():
    pass

@main.command()
def initdb():
    click.echo('Initialized the database')

@main.command()
def dropdb():
    click.echo('Dropped the database')

@main.command()
@click.option('--count', default=1, help='number of greetings')
@click.argument('name')
def whoami(count, name):
    for _ in range(count):
        click.echo('Hello %s!' % name)
        
@main.command()
def command_in_four_parts():
    click.echo('This is a command that spans four lines.')

if __name__ == "__main__":
    main()
