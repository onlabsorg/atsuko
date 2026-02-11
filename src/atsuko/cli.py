'''Module for creating command-line interfaces out of functions.

This module contains a class CLI for creating a command-line interface.

    >>> from atsuko import CLI
    >>> cli = CLI(name, description, version)

Once you create a cli, you need to add commands to it. Each function decorated
with `@cli.command` becomes a command that takes the functions parameters.
For example:

    >>> @cli.command
    ... def do_something (a, b, c):
    ...     ...
    ...
    >>> @cli.command
    ... def do_somehting_else (d, e):
    ...     ...

The first function will create a command that can be executed from the prompt
by thyping `this-script.py do-something a b c` while the second function will
be executed when entering `this-script.py do-something-else d e`.

In order to make the cli parse and execute the command-line parameters, the
`cli.run` function needs to be executed after defining all the commands:

    >>> cli.run(sys.argv[1:])

The CLI instances handle also automatic help messages, optional parameters and
every other syntax that can be defined with argparse. To do so, it leverages
python parameter annotations.

    >>> from atsuko import Param
    >>> @cli.command
    ... def echo (msg : Param("FullName", str, "Msg parameter description"),
    ...           cap : Param("Capitalize", bool, "Capitalize option description") = False):
    ... """Echo command help message
    ... 
    ... Detailed echo command help message that will be shown when
    ... the echo command is followed by --help or -h """
    ... 
    ... cli.log(msg.upper() if cap else msg)

In the previous example, the `msg` parameter is a positional parameter, while the
`cap` parameter is an optional parameter that at the command line can be passed as
`--cap` or as `-c`. What makes `cap` and optional parameter and `msg` not is the
presence of a default value.
'''

import os
import sys
from datetime import datetime
from dataclasses import dataclass
from functools import cached_property




class CLI:
    """A command-line interface.

    This class defines an application, consisting of a set of commands that can 
    be run via the command-line.

    Attributes:
        name: The application name.
        description: A description of the application.
        version: The application version.
    """

    def __init__ (self, name, description, version="1.0.0"):
        """Initializes the command-line application.

        Args:
            name (str): The application name.
            description (str): A description of the application, that will be used for 
                documentation purposes. When you write the description, you are 
                talking to the users of your application, explaining it to them.
            version (str): The application version, in semantic-versioning format.
                Defaults to "1.0.0".
        """
        self.name = name
        self.description = '\n'.join([line.strip() for line in description.split("\n") if line != ""])
        self.version = version
        self.commands = {}


    def log (self, message):
        """Logs a message to the console"""
        print(message)


    def command(self, func):
        """A decorator that turns a function into an application command.

        The decorated function can then be run via the command-line by passing 
        its name and its parameters after the script name. To enable that,
        the function cli.run needs to be called after defining the commands.

        Args:
            func: The function to be turned into a command.

        Returns:
            The command object.

        Examples:
            >>> @app.command
            ... def sum(a, b):
            ...     app.log(a + b)
            ...
            # The command can be invoked via the CLI as follows:
            # > py <script-name.py> sum 12 33
            # > 45
        """
        name = func.__name__.replace('_', '-')
        self.commands[name] = Command(name, func)
        return self.commands[name]


    def parse (self, args=sys.argv[1:]):
        """Parses a list of command-line tokens

        This method uses argparse internally to translate the commands defined
        with the .command decorator into a parser. Then executes the parser and
        returns its output.
        """
        import argparse

        # Create the top-level parser
        parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description
        )

        parser.add_argument(
            '-v', '--version',
            action='store_true',
            help="show the program version"
        )

        # Create the sub-parsers ...
        sub_parsers = parser.add_subparsers()

        # ... one for each command ...
        for command in self.commands.values():
            cmd_parser = sub_parsers.add_parser(
                command.name,
                help=command.description,
                description=command.documentation
            )

            # ... ... add parameters ...
            for param in command.parameters.values():

                if param.type == _VarArgs:  # Variable Positional Arguments
                    cmd_parser.add_argument(
                        param.name,
                        help=param.description,
                        nargs="*",
                        action='store'
                    )

                elif param.required:  # positional parameters
                    cmd_parser.add_argument(
                        param.name,
                        type=param.type,
                        help=param.description,
                        choices=param.choices,
                        action='store'
                    )

                elif param.type == bool:    # boolean flags
                    cmd_parser.add_argument(
                        f"--{param.name}",
                        help=param.description,
                        required=False,
                        action = 'store_false' if bool(param.default) else 'store_true'
                    )

                else:  # any other type of optional parameters
                    cmd_parser.add_argument(
                        f"--{param.name}",
                        type=param.type,
                        help=param.description,
                        required=False,
                        default=param.default,
                        choices=param.choices,
                        action='store'
                    )

        return parser.parse_args(args)


    def run (self, args=sys.argv[1:]):
        """Execute a command, given the command-line argument list.

        Args:
            args: A list of command-line arguments. Defaults to `sys.argv[1:]`.
        """
        # If the script is called without parameters,
        # print the help message
        if not args:
            self.parser.print_help()
            return

        # Parse the arguments
        argns = self.parse(args)

        # Detect the command
        command = self.commands.get(args[0], None)

        # Handle the case with no command
        if not command:

            if argns.version:
                self.log(self.version)

            return

        # Execute the command
        args, kwargs = command.split_parameters(vars(argns))
        command(*args, **kwargs)



@dataclass
class Command:
    """Represents a command in the application.

    This class is not meant to be instantiated directly. A command instance is 
    generated by the `cli.command` decorator and stored inside the `CLI` 
    instance.

    Attributes:
        name: The command name.
        func: The function associated with the command.
    """
    name: str                   # Te command name
    func: type(lambda: None)    # The function associated with the command

    @cached_property
    def _docstring(self):
        # This internal function parses the function dostring to extract
        # a short command description (first line of the docstring) and
        # a long command description (the rest of the docstring),

        # Retrieve the docstring and split it in separate lines
        import inspect
        docstring = inspect.getdoc(self.func) or self.name
        lines = docstring.split("\n")

        # If the dostring is only one line, that line is the short
        # description, while the long description will be empty.
        if len(lines) == 1:
            description = docstring
            documentation = ""

        # If the second line is empty, this is interpreted as a
        # separator, so the first line will be the short description
        # and the lines from 3rd to last will be the long description.
        elif lines[1] == "":
            description = lines[0]
            documentation = "\n".join(lines[2:])

        # In any other situation, the short description will be a
        # standard "Command <name>" and the docstring will be
        # interpreted as long description.
        else:
            description = f"Command {self.name}"
            documentation = docstring

        # Return both short and long description.
        return description, documentation

    @cached_property
    def description(self):
        """Short description extracted from the docstring."""
        description, documentation = self._docstring
        return description
        
    @cached_property
    def documentation(self):
        """Long description extracted from the docstring."""
        description, documentation = self._docstring
        return documentation

    @cached_property
    def parameters(self):
        """A dictionary of parameters for this command.

        The keys are the parameter names and the values are `Parameter` objects.
        """
        import inspect
        params = inspect.signature(self.func).parameters
        return {
            param_name: CommandParameter(param_info)
            for param_name, param_info in params.items()
        }

    def split_parameters(self, params):
        """Split parameters into positional and keyword arguments.

        Groups the passed parameters dictionary in a list of positional 
        parameter name and a dictionary of options, so that they can be passed 
        as `args` and `kwargs` to the `__call__` method.

        Args:
            params: A dictionary of parameters.

        Returns:
            A tuple containing a list of positional arguments and a dictionary 
            of keyword arguments.
        """
        args = [params[name] for name, param in self.parameters.items() if param.required]
        kwargs = {name: params[name] for name, param in self.parameters.items() if not param.required and param.type != _VarArgs}
        for name, param in self.parameters.items():
            if param.type == _VarArgs:
                args += params[name]
        return args, kwargs

    def __call__(self, *args, **kwargs):
        """Call the command's function.

        This class is also a callable. Calling the class instance is equivalent 
        to calling command.func.
        """
        return self.func(*args, **kwargs)


class CommandParameter:
    """Information about a command parameter.

    This class should not be instantiated directly. It is instead called by the 
    Command class when creating a command from a function and parsing its 
    parameters.

    Attributes:
        name: The parameter name.
        pretty_name: A human-readable name to be used for documentation.
        type: The expected type of the parameter (e.g. str, int, bool, etc.).
        description: A description of the parameter to be used for documentation.
        choices: A list of valid values for the parameter.
        required: True if the parameter is not optional (meaning it doesn't have a
            default value).
        default: The default value for optional parameters.
    """

    def __init__ (self, param_info):
        """Initializes the Parameter.

        Args:
            param_info: An `inspect.Parameter` object.
        """
        import inspect
        EMPTY = inspect._empty

        # Parameter name
        self.name = param_info.name

        # Validate the parameter type
        if param_info.kind == inspect.Parameter.VAR_KEYWORD:
            raise TypeError("Variable number of optional arguments not supported")

        # Extract the user-defined annotation parameters
        if isinstance(param_info.annotation, ParameterAnnotation):
            self.pretty_name = param_info.annotation.name
            self.type = param_info.annotation.type
            self.description = param_info.annotation.description
            self.choices = param_info.annotation.choices

        elif isinstance(param_info.annotation, type) and param_info.annotation != EMPTY:
            self.pretty_name = self.name
            self.type = param_info.annotation
            self.description = f"Parameter '{self.name}' of {str(self.type_name)}"
            self.choices = None

        elif param_info.default != EMPTY and param_info.default != None:
            self.pretty_name = self.name
            self.type = type(param_info.default)
            self.description = f"Parameter '{self.name}' of {str(self.type_name)}"
            self.choices = None

        else:
            self.pretty_name = self.name
            self.type = str
            self.description = f"Parameter '{self.name}' of {str(self.type_name)}"
            self.choices = None

        # Define if the parameter is required (doesn't have a default value)
        # and if not, defines its default value.
        if param_info.default == EMPTY:
            self.required = True
            self.default = None
        else:
            self.required = False
            self.default = param_info.default

        # Modify thype and default value in case of variable positional arguments
        if param_info.kind == inspect.Parameter.VAR_POSITIONAL:
            self.type = _VarArgs
            self.required = False
            self.default = []


    @cached_property
    def type_name(self):
        """A pretty name for this parameter type."""
        if self.type == str:
            return "Text"
        elif self.type == int or self.type == float:
            return "Number"
        elif self.type == bool:
            return "Boolean"
        elif self.type == _VarArgs:
            return "ListOfArguments"
        else:
            return str(self.type)


class _VarArgs (list):
    # Type used internally by the Parameter class
    # to identify variable positional arguments.
    pass



@dataclass
class ParameterAnnotation:
    """A namespace for command parameter information.

    When defining a command, an instance of this class can be associated to
    the parameter as an annotation.

    Attributes:
        name: A pretty name for the command to be used in the GUI and documentation.
        type: The parameter type. Supported types are currently `str`, `int`,
            `float`, and `bool`. All other types are treated as strings.
        description: A description of the parameter to be used for documentation purposes.
        choices: A list of allowable values for the parameter.

    Examples:
        >>> @clo.command
        ... def sum(
        ...     a: Parameter(
        ...         name="Addend1",
        ...         type=float,
        ...         description="First addend."
        ...     ),
        ...     b: Parameter(
        ...         name="Addend2",
        ...         type=float,
        ...         description="Second addend."
        ...     ),
        ...     prec: Parameter(
        ...         name="Precision",
        ...         type=int,
        ...         description="Result decimal precision, default to 2"
        ...     ) = 2
        ... ):
        ...     cli.log(round(a + b, prec))
    """

    name: str
    type: type = str
    description: str = ""
    choices: list = None


