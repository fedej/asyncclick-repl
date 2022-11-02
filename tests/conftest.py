import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    output = DummyOutput()
    output.fileno = lambda: 1
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=output):
            yield pipe_input
