# asyncclick-repl

Command to make a REPL out of a group by passing `-i` or `--interactive` to the cli.
Inspired by [click-repl](https://github.com/click-contrib/click-repl) but using native
click command and shell completion.

```python
import asyncio

import asyncclick as click

from asyncclick_repl import AsyncREPL


@click.group(cls=AsyncREPL)
async def cli():
    pass


@cli.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
async def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        await asyncio.sleep(0.1)
        click.echo(f"Hello, {name}!")


cli(_anyio_backend="asyncio")
```

```shell
myclickapp -i

> hello --count 2 --name Foo
Hello, Foo!
Hello, Foo!
> :q
```

# Features:

- Tab-completion. Using click's shell completion
- Execute system commands using `!` prefix. Note: `!` should be followed by a space e.g `! ls`
- `:h` show commands help.

# Prompt configuration

Use `prompt_kwargs` to provide configuration to `python-prompt-toolkit`'s `Prompt` class

```python
import asyncclick as click
from prompt_toolkit.history import FileHistory

from asyncclick_repl import AsyncREPL

prompt_kwargs = {
    "history": FileHistory("./history"),
}


@click.group(cls=AsyncREPL, prompt_kwargs=prompt_kwargs)
async def cli():
    pass


cli()
```
