import pytest
from testfixtures import TempDirectory

from shoehorn.testing import capture

@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir
