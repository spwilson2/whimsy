# Overview of Files

## Main Function Modules

Files are listed in order of relative importance and are slightly categorized.
See each file's module docstring for more details.

### `main.py`

The main entrypoint for whimsy. Uses parsed command-line arguments to direct
the flow of the program execution.

### `loader.py`

Contains the `TestLoader` class which implements logic for discovering and
parsing test files for their different test items.

### `runner.py` 

Contains the `Runner` class. This class is responsible for running all
`TestCase` and `TestSuite` instances, setting up `Fixture` objects, and
notifying registered `ResultLogger` objects of test results as they are run.

## Testing Items

### `suite.py`

Contains the definition of a `TestSuite` class - a completely self-contained
unit of test. Also implents containers for `TestSuite` and `TestCase` instances
(`SuiteList` and `TestList` respectively) which provide utility methods and
supply some metadata about contained objects.

### `test.py`

Defines the base abstract `TestCase` class and the concrete `TestFunction`
class which is a `TestCase` that runs a single function. Also provides
a function decorator `testfunction` which provides a simple interface to
create a `TestFunction` instance.

### `fixture.py`

Defines the base class for a `Fixture`

## Support Files

### `result.py`

Contains various classes implementing the `ResultLogger` logger interface which
the runner uses to report results. This is the method used to collect and
report test results as they happen or once all testing is complete.

### `config.py`

Contains a global `config` object used to configure options throughout tests.
Stores defaults, constants and parses commandline arguments.

### `logger.py`
### `tee.py`
### `terminal.py`
### `queury.py`
### `util.py`
