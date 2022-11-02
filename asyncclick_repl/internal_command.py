import subprocess
from contextlib import contextmanager
from typing import Any, List, Optional

import anyio
import asyncclick as click
from asyncclick import get_current_context
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.contrib.completers import SystemCompleter
from prompt_toolkit.document import Document


class SystemCommand(click.Command):
    def __init__(self):
        super().__init__("!", help="Run external commands", hidden=True)
        self._system_completer = SystemCompleter()

    async def invoke(self, ctx: click.Context) -> Any:
        try:
            result = await anyio.run_process(" ".join([*ctx.args]))
            click.echo(result.stdout, nl=False)
        except subprocess.CalledProcessError as e:
            click_exception = click.exceptions.ClickException(str(e))
            click_exception.exit_code = e.returncode
            raise click_exception from e

    async def make_context(
        self,
        info_name: Optional[str],
        args: List[str],
        parent: Optional[click.Context] = None,
        **extra: Any,
    ) -> click.Context:
        return await super().make_context(
            info_name,
            args,
            parent=parent,
            ignore_unknown_options=True,
            allow_extra_args=True,
            **extra,
        )

    def shell_complete(
        self, ctx: click.Context, incomplete: str
    ) -> List[click.shell_completion.CompletionItem]:
        document = Document(incomplete)
        return [
            click.shell_completion.CompletionItem(c.text)
            for c in self._system_completer.get_completions(
                document, CompleteEvent(completion_requested=True)
            )
        ]


@contextmanager
def visible_internal_commands(group: click.Group, ctx: click.Context):
    internal_commands = [
        c for c in group.list_commands(ctx) if c.startswith(":") or c == "!"
    ]
    try:
        for command in internal_commands:
            cmd = group.get_command(ctx, command)
            if cmd:
                cmd.hidden = False
        yield
    finally:
        for command in internal_commands:
            cmd = group.get_command(ctx, command)
            if cmd:
                cmd.hidden = True


def register_internal_commands(command: click.Group):
    def show_help():
        ctx = get_current_context().parent
        with visible_internal_commands(command, ctx):
            formatter = ctx.make_formatter()
            command.format_commands(ctx, formatter)
            click.echo(formatter.getvalue().rstrip("\n"), color=ctx.color)

    command.add_command(
        click.Command(
            ":h",
            callback=show_help,
            hidden=True,
            help="Display general help information",
        )
    )

    def _exit():
        raise click.exceptions.Exit(0)

    command.add_command(
        click.Command(":q", hidden=True, callback=_exit, help="Exit the REPL")
    )

    command.add_command(
        click.Command(
            ":c", hidden=True, callback=lambda: click.clear(), help="Clear the screen"
        )
    )
