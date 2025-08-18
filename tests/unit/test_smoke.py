"""Basic smoke tests to ensure the test runner and package import work."""


def test_package_imports() -> None:
    import qraft  # noqa: F401  # ensure package can be imported

    assert True