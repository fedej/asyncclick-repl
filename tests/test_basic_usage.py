import asyncio

import asyncclick as click
import pytest
from asyncclick.testing import CliRunner
from prompt_toolkit.input.base import PipeInput

from asyncclick_repl import AsyncREPL


@pytest.fixture
def cli_group():
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

    @cli.command()
    async def fail():
        """Just fail"""
        raise RuntimeError("Failed!")

    return cli


async def test_calls_hello(mock_input: PipeInput, cli_group):
    runner = CliRunner()
    mock_input.send_text("hello --count 4 --name test\n:q\n")
    result = await runner.invoke(cli_group, ["-i"])

    assert result.exit_code == 0
    assert (
        result.output
        == """Hello, test!
Hello, test!
Hello, test!
Hello, test!
"""
    )


async def test_gets_help(mock_input: PipeInput, cli_group):
    runner = CliRunner()
    mock_input.send_text(":h\n:q\n")
    result = await runner.invoke(cli_group, ["-i"])

    assert result.exit_code == 0
    assert (
        result.output
        == """Commands:
  !      Run external commands
  :c     Clear the screen
  :h     Display general help information
  :q     Exit the REPL
  fail   Just fail
  hello  Simple program that greets NAME for a total of COUNT times.
"""
    )


async def test_runs_system_command(mock_input: PipeInput, cli_group):
    runner = CliRunner()
    mock_input.send_text("! ls\n:q\n")

    with runner.isolated_filesystem():
        with open("hello.txt", "w"):
            result = await runner.invoke(cli_group, ["-i"])

    assert result.exit_code == 0
    assert result.output == "hello.txt\n"


async def test_runs_failing_system_command(mock_input: PipeInput, cli_group):
    runner = CliRunner()
    mock_input.send_text("! ls && false\n:q\n")

    with runner.isolated_filesystem():
        with open("hello.txt", "w"):
            result = await runner.invoke(cli_group, ["-i"])

    assert result.exit_code == 0
    assert result.output == (
        "Error: Command 'ls && false' returned non-zero exit status 1.\n"
    )


async def test_non_interactive(cli_group):
    runner = CliRunner()
    result = await runner.invoke(cli_group, ["hello"], input="Test")

    assert result.exit_code == 0
    assert result.output == "Your name: Test\nHello, Test!\n"


async def test_prints_error_and_continues(mock_input: PipeInput, cli_group):
    runner = CliRunner()
    mock_input.send_text("fail\nhello --name test\n:q\n")

    result = await runner.invoke(cli_group, ["-i"])

    assert result.exit_code == 0
    assert "Traceback (most recent call last)" in result.output
    assert 'raise RuntimeError("Failed!")' in result.output
    assert "RuntimeError: Failed!" in result.output
    assert "Hello, test!" in result.output
