# Whimsy

Test Framework for [gem5](http://gem5.org).

## Overview

### Running Tests

To run all tests use the test subcommand like so (Assuming in gem5/tests/ not
included in this repository.):

```bash
./main.py run example
```

The test subcommand has some optional flags: 
* `--skip-build` to skip the building of scons targets. (Like gem5)
* `-v` increase verbosity level once per flag.
* `--uid` run the test item with the given uid (TODO)
* `-h` Show help and list more available flags.

### Typical Runloop

In a typical run of whimsy using the run subcommand. Whimsy will first parse
the command line flags. Assuming the run command is given, whimsy will then
create a `TestLoader` object and use that object to collect all tests in the
given `directory`.

#### Test Collection/Discovery Step

The `TestLoader` will recurse down the directory tree looking for test program
file names that match the `default_filepath_regex`. Python files that either
begin or end in `test` or `tests` with a hyphen or underscore will match.  e.g.
`test-something.py` or `special-tests.py` will match, but `tests.py` will not.
Additionally, 'hidden' files that begin with a `.` will be ignored.

Once the `TestLoader` has found a file that has a name indicating it is a test
program, the loader will begin to load tests from that file by calling
`execfile` on it. `TestCase` instances and `TestSuite` objects in the test file
will be collected automatically. Any `TestCase` objects which are not
specifically placed into a `TestSuite` instance will be collected into
a `TestSuite` created for the module.

##### Digression on collection implementation.

Actual collection of tests is done by modifying the `__init__` methods of
objects that the loader is attempting to collect (`Fixture`, `TestCase` and
`TestSuite` instances). It also attaches a `__rem__` function to these classes
as well. `__rem__` can be used to uncollect collected items. (Users should
instead use the `loader.no_collect` function to do this instead of the member
member function.)

In addition to executing the original `__init__` implementation of these
classes, the modified `__init__` call also adds instances to an `OrderedSet` in
the loader. If the user then calls `no_collect` on a test item, the item is
removed from the `OrderedSet` in the `TestLoader` and effectively will not be
collected.


#### Test Running Step

Once the tests have been discovered and collected by the `TestLoader`,
`main.py` will create the requested `ResultLogger` logger objects used to
display results and/or stream them into a file in a specified format.
(Currently an `ConsoleLogger`, `InternalLogger`, `JUnitLogger` exist). All
loggers are designed to minimize the amount of memory used by writing out test
information as soon as possible rather than storing large strings.

With these formatters and the `SuiteList` of `TestSuite` objects find by the
loader, the `Runner` object is instantiated.

The `Runner` first sets up any `Fixture` objects that are not `lazy_init`.
Once all these `lazy_init` fixtures have been set up the `Runner` begins to
iterate through its suites.

The run of a suite takes the following steps:

1. Iterate through each `TestCase` passing suite level fixtures to them and
   running them.
2. If the `TestCase` fails, check `fail_fast` conditions and fail out if one 
   occurs.
    * A `TestSuite` or the containing `TestList` was marked `fail_fast`
    * The `--fail-fast` flag was given as a command line arg.
3. `teardown` any built fixtures contained in the `TestSuite` object.


The run of a `TestCase` follows these steps:

1. Start capturing stdout and stderr logging it into separate files.
2. Copy the suites fixtures and overwrite them with any versions we have in
   this test case.
3. Build all the fixtures that are required for this test.
    * If any fixture build fails by throwing an exception, mark the test as
      failed.  
4. Execute the actual test function, catching all exceptions. 
    * Any exception other than the `TestSkipException` thrown by the
      `test.skip` function will result in a fail status for the test.
    * The test passes if no exceptions are thrown and the `__call__` returns.


Reporting of test results is done as tests are being ran.

## Test Writing By Example


### Writing A Verifier Test

### Running Your Test


## Writing Your Own Test

### Adding Fixtures
