import shlex
import traceback
from typing import Any, Dict, List, Optional

import asyncclick as click
import asyncclick.exceptions
from asyncclick.shell_completion import CompletionItem
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from asyncclick_repl.completer import ShellCompleter
from asyncclick_repl.internal_command import (
    SystemCommand,
    register_internal_commands,
    visible_internal_commands,
)


class AsyncREPL(click.Group):
    def __init__(
        self, name: Optional[str], prompt_kwargs: Dict[str, Any] = None, **kwargs: Any
    ):
        allow_system_commands = kwargs.pop("allow_system_commands", True)
        params = kwargs.pop("params", []) or [
            click.Option(
                ["-i", "--interactive"],
                is_flag=True,
                flag_value=True,
                type=click.types.BoolParamType(),
                help="Run interactive shell",
            )
        ]
        super().__init__(name, invoke_without_command=True, params=params, **kwargs)
        prompt_session_kwargs = {
            "history": InMemoryHistory(),
            "completer": ShellCompleter(self),
            "complete_while_typing": False,
            "message": "> ",
        }
        if prompt_kwargs:
            prompt_session_kwargs.update(prompt_kwargs)

        self._session = PromptSession(**prompt_session_kwargs)  # type: ignore
        if allow_system_commands:
            self.add_command(SystemCommand())
        register_internal_commands(self)

    async def invoke(self, ctx: click.Context) -> Any:
        if not ctx.params.pop("interactive", False):
            self.invoke_without_command = False
            return await super().invoke(ctx)

        while True:
            try:
                command = await self._session.prompt_async()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            if not command:
                continue

            try:
                args = shlex.split(command)
            except ValueError as e:
                click.secho(
                    f"Error: {type(e).__name__} {e}", err=True, color=True, fg="red"
                )
                continue

            try:
                async with await self.make_context(
                    None, args, parent=ctx, color=True
                ) as new_ctx:
                    new_ctx.params.pop("interactive")
                    await super().invoke(new_ctx)
            except click.UsageError as e:
                click.secho(
                    f"Error: {e.format_message()}", color=True, err=True, fg="red"
                )
            except click.ClickException as e:
                e.show()
            except asyncclick.exceptions.Exit as e:
                raise e
            except SystemExit:
                pass
            except Exception:
                traceback.print_exc()

    def shell_complete(
        self, ctx: click.Context, incomplete: str
    ) -> List[CompletionItem]:
        if incomplete.startswith(":"):
            with visible_internal_commands(self, ctx):
                return super().shell_complete(ctx, incomplete)
        return super().shell_complete(ctx, incomplete)
