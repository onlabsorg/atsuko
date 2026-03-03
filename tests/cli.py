from atsuko import CLI, Param


cli = CLI("Test app", "Test atsuko application", "0.1.0")


@cli.command
def docs (param_with_no_annotation,
          param_with_type_annotation: int,
          param_with_text_annotation: "Parameter with text annotation",
          param_with_full_annotation: Param(float, "Parameter with full annotation")):
    '''Documentation test

    This command has 3 parameters: the fists defined with no annotation,
    the second defined with just a type as annotation and the third
    defined with a Param instance as annotation. Check if the help message
    has been correctly built accordingly.
    '''

    cli.log("Run this command with the --help flag to test it")


@cli.command
def vals (s: Param(str, "Positional parmaeter of string type"),
          n: Param(float, "Positional parmaeter of float type"),
          opt_s: Param(str, "Optional string parameter, defaulting to 'boo'")="boo",
          opt_t: Param(bool, "Optional bool param, defaulting to True")=True,
          opt_f: Param(bool, "Optional bool param, defaulting to False")=False,
          opt_e: Param(str, "Enumerated parameter of type stricng", choices=['A','B','C']) = 'A',
          ):
          #opt_s: Param(str, "Optional string parameter defaulting to 'boo'")="boo"):
    '''Test parameters values

    This command contains optional and positional parameters and it
    print the value and type of the corresponding arguments.
    '''
    cli.log(f"s = {s} [{type(s)}]")
    cli.log(f"n = {n} [{type(n)}]")
    cli.log(f"opt-s = {opt_s} [{type(opt_s)}]")
    cli.log(f"opt-t = {opt_t} [{type(opt_t)}]")
    cli.log(f"opt-f = {opt_f} [{type(opt_f)}]")
    cli.log(f"opt-e = {opt_e} [{type(opt_e)}]")


@cli.command
def add (a: Param(float, "First addend"),
         b: float):
    '''Sum two numbers

    Prints the sum of the two passed numbers
    '''
    cli.log(a + b)


if __name__ == "__main__":
    cli.run()
