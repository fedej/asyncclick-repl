import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    pipe_input = create_pipe_input()
    try:
        output = DummyOutput()
        output.fileno = lambda: 1
        with create_app_session(input=pipe_input, output=output):
            yield pipe_input
    finally:
        pipe_input.close()
