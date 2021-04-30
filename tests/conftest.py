import pytest
import logging


@pytest.fixture
def logger():
    return logging.getLogger(__name__)
