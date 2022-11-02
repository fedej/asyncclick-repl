import shlex
from typing import AsyncGenerator, Iterable, List, Tuple

import asyncclick as click
from asyncclick.shell_completion import CompletionItem, ShellComplete
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    PathCompleter,
)
from prompt_toolkit.document import Document


class ShellCompleter(Completer):
    class _FakeShellComplete(ShellComplete):
        def __init__(self, cli: click.BaseCommand) -> None:
            super().__init__(cli, {}, "", "")

        def get_completion_args(self) -> Tuple[List[str], str]:
            return [], ""

        def format_completion(self, item: CompletionItem) -> str:
            return f"{item.type},{item.value}"

    def __init__(self, command: click.BaseCommand):
        self.completion = self._FakeShellComplete(command)
        self.path_completer = PathCompleter(only_directories=False, expanduser=True)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        raise NotImplementedError  # asyncclick only supports `async get_completions`

    async def get_completions_async(
        self, document: Document, complete_event: CompleteEvent
    ) -> AsyncGenerator[Completion, None]:
        args = shlex.split(document.text_before_cursor)
        incomplete = (
            args.pop()
            if args
            and (document.text_before_cursor.rstrip() == document.text_before_cursor)
            else ""
        )

        for c in await self.completion.get_completions(args, incomplete):
            if c.type in ["file", "dir"]:
                new_document = Document(incomplete, cursor_position=-len(incomplete))
                for comp in self.path_completer.get_completions(
                    new_document, complete_event
                ):
                    yield comp
            elif c.value != "--help":
                yield Completion(
                    c.value, start_position=-len(incomplete), display_meta=c.help
                )
