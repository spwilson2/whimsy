Whimsy
======

Test Framework for `gem5 <http://gem5.org>`__.

Running Tests
-------------

To run all tests use the ``run`` subcommand:

.. code:: bash

    ./main.py run . # The '.' is optional.

The ``run`` subcommand has some optional flags: 

- ``--skip-build`` skip the building of scons targets (like gem5) 
- ``-v`` increase verbosity level once per flag. 
- ``--uid`` run the test item with the given uid.
- ``-h`` Show help and list more available flags.

Motivation
----------

**Note:** This section is non-normative.

A testing infrastructure already exists for Gem5. Why create a new one? There
are quite a few issues which exist in the current infrastructure. Just to list
the worst and most prevalent issues.

1. The system is scattered across multiple systems.

   - No center location for documentation/information
     
   - Mulitiple entrypoints to the testing system.
 
   - Massive amounts of indirection between scons, config files, and the
     current framework

2. There is not a simple way to add requirements for tests. If they need
   something set up, one has to muck around the gem5 build system.

3. 

Definition of Terms
-------------------

There are a few terms used in this documentation that readers may not be
familiar with. The purpose of this section is to briefly introduce new users to
these.

Test Suite
~~~~~~~~~~

A :class:`whimsy.suite.TestSuite` is a completely self-contained unit of
testing which must contain one or more `TestCase <#test-case>`__ instances.
Test suites can rely on `Fixtures <#fixture>`__, have `tags
<#tags>`__ (which contained test cases will be tagged with), and be marked
`fail\_fast <#fail-fast>`__.

Test Case
~~~~~~~~~

A :class:`whimsy.test.TestCase` is a unit of test that is not necessarily
self-contained. An example of a test which is not self contained would be
a test which parses the output of a gem5 run against a gold standard. Since
this test case relies on gem5 running first, it would no longer pass if ran on
its own and therfore the test is not self-contained.

.. note:: Test cases can also have all the metadata that a test suite has (Tags
    and Fixtures). (However they cannot be individually marked `fail\_fast
    <#fail-fast>`__)

Fixture
~~~~~~~

A :class:`whimsy.fixture.Fixture` is an object that may require setup or
tearing down before or after a `TestCase <#test-case>`__ or `TestSuite
<#test-suite>`__ has run. When tests are run, they will be handed fixtures from
their containing TestSuite, and will set up any fixtures that are not already
built. This allows test cases to incrementally test results of gem5 runs.

Most importantly Fixtures remove the requirement on SCons to keep track of test
requirements. TestCases and TestSuites now maintain that information on their
own and the runner will make an aggregated call to SCons on their behalf.

Tags
~~~~

Tags are used to mark groups of related tests. Common examples of tags are ISA
(`X86`, `ARM`), testing length (`quick`, `long`), and system emulation type
(`se`, `fs`). Indexes of tags are built by the
:class:`whimsy.loader.TestLoader` to query and run tests by specifying command
line arguments.

Fail Fast
~~~~~~~~~

Fail Fast (written ``fail_fast`` throughout this document) has slightly
different semantics depending on the use case. In general it means that given
a `TestCase` failure, refrain from testing some future number of tests.

The three different semantics are as follows:

1. The ``--fail-fast`` flag during the run of tests will cause all remaining
   tests to be ignored. 

   The use case for this could be a script that just checks on commit if all
   tests pass or not. If they don't pass we avoid wasting time running the
   remaining tests. 

2. While executing a ``TestSuite`` that is marked ``fail_fast``, if a
   ``TestCase`` in that suite fails then the remaining tests in that
   TestSuite will be skipped. If there are any remaining TestSuites to run,
   they will continue to run.

3. Inside of a ``TestSuite``, test cases are stored in hierarchical
   :class:`whimsy.suite.TestList` objects. In addition to utility functions
   ``TestList`` instances have a ``fail_fast`` attribute. When a test fails in
   a ``TestList`` the remaining test cases in that TestList will be skipped.
   However, if there are any remaining test lists or cases outside of the
   failed one, inside of the currently executing TestSuite, they will still be
   executed.

This last case visually:

-  TestList
-  Gem5 Run `(FAILS)`
-  TestList `(Will all be skipped)`

   -  TestStdout `(skipped)`
   -  TestStderr `(skipped)`


.. note:: The use case for the ``TestSuite`` ``fail_fast`` option is more one
    of convinience. Its semantics differ slightly from the ``TestList`` use,
    but in the general case it just allows users to create a TestSuite and
    TestCases without an intermediate ``TestList``.

File Organization
-----------------

Typical Runloop
---------------

In a typical run of whimsy using the run subcommand. Whimsy will first parse
the command line flags. Assuming the run command is given, whimsy will then
create a :class:`whimsy.loader.TestLoader` object and use that object to
collect all tests in the given directory.

.. seealso:: For more info see :mod:`whimsy.main`

Test Collection and Discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``TestLoader`` will recurse down the directory tree looking for test
program file names that match the ``default_filepath_regex``. Python files that
either begin or end in ``test`` or ``tests`` with a hyphen or underscore will
match. e.g. ``test-something.py`` or ``special-tests.py`` will match, but
``tests.py`` will not.  Additionally, 'hidden' files that begin with a ``.``
will be ignored. 

Once the ``TestLoader`` has found a file that has a name indicating it
is a test program, the loader will begin to load tests from that file by
calling ``execfile`` on it. ``TestCase`` instances and ``TestSuite``
objects in the test file will be collected automatically. Any
``TestCase`` objects which are not specifically placed into a
``TestSuite`` instance will be collected into a ``TestSuite`` created
for the module.

.. seealso:: For more info on discovery, valid filenames, and collection see
    :mod:`whimsy.loader`

Test Running Step
~~~~~~~~~~~~~~~~~

Once the tests have been discovered and collected by the ``TestLoader``,
:mod:`whimsy.main` will create the requested
:class:`whimsy.result.ResultLogger` logger objects used to display results
and/or stream them into a file in a specified format. (Currently an
``ConsoleLogger``, ``InternalLogger``, ``JUnitLogger`` exist). All loggers are
designed to minimize the amount of memory used by writing out test information
as soon as possible rather than storing large strings.

With these formatters and the ``SuiteList`` of ``TestSuite`` objects
find by the loader, the ``Runner`` object is instantiated.

The ``Runner`` first sets up any ``Fixture`` objects that are not
``lazy_init``. Once all these ``lazy_init`` fixtures have been set up
the ``Runner`` begins to iterate through its suites.

The run of a suite takes the following steps:

1. Iterate through each ``TestCase`` passing suite level fixtures to
   them and running them.
2. If the ``TestCase`` fails, check ``fail_fast`` conditions and fail
   out if one occurs.

   -  A ``TestSuite`` or the containing ``TestList`` was marked
      ``fail_fast``
   -  The ``--fail-fast`` flag was given as a command line arg.

3. ``teardown`` any built fixtures contained in the ``TestSuite``
   object.

The run of a ``TestCase`` follows these steps:

1. Start capturing stdout and stderr logging it into separate files.
2. Copy the suites fixtures and overwrite them with any versions we have
   in this test case.
3. Build all the fixtures that are required for this test.

   -  If any fixture build fails by throwing an exception, mark the test
      as failed.

4. Execute the actual test function, catching all exceptions.

   -  Any exception other than the :class:`whimsy.test.TestSkipException`
      thrown by the :func:`whimsy.test.skip` function will result in a fail
      status for the test.

   -  The test passes if no exceptions are thrown and the ``__call__`` returns.

Reporting of test results is done as tests are ran.
