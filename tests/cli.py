from atsuko import CLI, Param


cli = CLI("Test app", "Test atsuko application", "0.1.0")


@cli.command
def test ():
    cli.log("test command")


@cli.command
def echo (msg: Param(str, "The message to be echoed to the console")):
    ''' Print a message to the console

    This command prints the given parameter to the console
    '''
    cli.log(msg)


@cli.command
def add (a, b):
    ''' Sum a list fo numbers

    Given a list of numbers, print the sum of those numbers.
    '''
    cli.log(float(a)+float(b))


if __name__ == "__main__":
    cli.run()
