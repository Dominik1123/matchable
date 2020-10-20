import nox


nox.options.sessions = 'lint', 'tests'
file_locations = 'src',


@nox.session(python='3.8')
def coverage(session):
    session.install('coverage[toml]', 'codecov')
    session.run('coverage', 'xml', '--fail-under=0')
    session.run('codecov', *session.posargs)


@nox.session(python='3.8')
def lint(session):
    flake8_args = session.posargs or file_locations
    session.install(
        'darglint',
        'flake8',
        'flake8-black',
        'flake8-docstrings',
    )
    session.run('flake8', *flake8_args)


@nox.session(python=['3.8', '3.7'])
def mypy(session):
    mypy_args = session.posargs or file_locations
    session.install('mypy')
    session.run('mypy', *mypy_args)


@nox.session(python=['3.8', '3.7'])
def tests(session):
    pytest_args = session.posargs or ['--cov']
    session.run('poetry', 'install', external=True)
    session.run('pytest', *pytest_args)
