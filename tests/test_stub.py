import pytest
import ic.cert


def test_create_object(logger):
    cd = ic.cert.Cert(logger=logger, server="localhost")
    assert isinstance(cd, ic.cert.Cert)
