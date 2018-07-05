import pytest
from testfixtures import TempDirectory


@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir
