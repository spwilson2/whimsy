Whimsy
======

Test Framework for `gem5 <http://gem5.org>`__.

Overview
--------

.. contents:: :depth: 2

Running Tests
~~~~~~~~~~~~~

To run all tests use the test subcommand like so (Assuming in
gem5/tests/ not included in this repository.):

.. code:: bash

    ./main.py run gem5

The test subcommand has some optional flags: \* ``--skip-build`` to skip
the building of scons targets. (Like gem5) \* ``-v`` increase verbosity
level once per flag. \* ``--uid`` run the test item with the given uid.
\* ``-h`` Show help and list more available flags.

Definition of Common Terms
~~~~~~~~~~~~~~~~~~~~~~~~~~

Test Suite
^^^^^^^^^^

A :class:`whimsy.suite.TestSuite` is a completely self-contained unit of
testing which must contain one or more `TestCase <#test-case>`__ instances.
Test suites can rely on `Fixtures <#fixture>`__ , have `tags
<#tags>`__ (which contained test cases will be tagged with), and be marked
`fail\_fast <#fail-fast>`__.

Test Case
^^^^^^^^^

A :class:`whimsy.test.TestCase` is not a unit of test that is not necessarily
self-contained. An example of not being self contained would be a test which
parses the output of a gem5 run for a specific config checking that its output
matches a known gold standard. Since this test case relies on gem5 running
first, it would no longer pass if ran on its own and is therfore not
self-contained.

Test cases can also have all the metadata that a test suite has (Tags and
Fixtures). However they cannot be marked `fail\_fast <#fail-fast>`__

Fixture
^^^^^^^

A :class:`whimsy.fixture.Fixture` is an object that may require setup and/or
tearing down after a `TestCase <#test-case>`__ or a `TestSuite <#test-suite>`__
has run. When tests are run, they will be handed fixtures from their containing
TestSuite, and will set up any fixtures that are not already built. This allows
test cases to incrementally test results of gem5 runs or perform other
incremental testing.

Most importantly Fixtures remove the requirement on SCons to keep track
of test requirements. TestCases and TestSuites now maintain that
information on their own and the runner will make an aggregated call to
SCons on their behalf.

Tags
^^^^

Tags are used to mark groups of related tests. Common examples of tags
are ISA (X86, ARM, etc.), testing length (quick, long, etc.), and system
emulation type (se,fs). Indexes of tags are built by the ``TestLoader``
to query and run tests by specifying command line arguments.

Fail Fast
^^^^^^^^^

Fail Fast (often written ``fail_fast`` here) has slightly different
semantics depending on the use case. In general it means that given a
failure quickly stop doing something.

The three different semantics are as follows:

1. The ``--fail-fast`` flag during the run of tests will cause all remaining
   tests to be ignored.

2. While executing a ``TestSuite`` that is marked ``fail_fast``, if a
   ``TestCase`` in that suite fails then the remaining tests in that
   TestSuite will be skipped. If there are any remaining TestSuites to run,
   they will continue to run.

3. Inside of a ``TestSuite``, test cases are stored in hierarchical
   :class:`whimsy.suite.TestList` objects. In addition to some utility
   functions ``TestList`` instances have a ``fail_fast`` attribute. When a
   test fails in a TestList the remaining Test cases in that TestList will be
   skipped. However, If there are any remaining test lists or cases outside of
   the failed one, inside of the currently executing TestSuite, they will
   still be executed.

Visually:

-  TestList
-  Gem5 Run (FAILS)
-  TestList (Will all be skipped)

   -  TestStdout (skipped)
   -  TestStderr (skipped)

File Organization
-----------------


Typical Runloop
~~~~~~~~~~~~~~~

In a typical run of whimsy using the run subcommand. Whimsy will first parse
the command line flags. Assuming the run command is given, whimsy will then
create a :class:`whimsy.loader.TestLoader` object and use that object to
collect all tests in the given directory.

Test Collection/Discovery Step
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. note:: See the documentation in the :mod:`whimsy.loader` module for more
    information on how items are actually collected and more examples of valid
    filenames.

Test Running Step
^^^^^^^^^^^^^^^^^

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

Test Writing By Example
-----------------------

Writing A Verifier Test
~~~~~~~~~~~~~~~~~~~~~~~

Since all testing in gem5 right now entirely follows the same format,
(run a config of gem5, then compare output to a known standard) Whimsy
tries to make this common case simple and the intent explicit. Whimsy
provides a general utility function :func:`whimsy.gem5.suite.gem5_verify_config` and mixin
:class:`whimsy.gem5.verifier.Verifier` classes.

Let's create a simple test which can runs gem5 and a config file for all
ISAs and optimization versions and checks that the exit status of gem5
was 0.

.. code:: python

    from testlib import *

    verifier = VerifyReturncode(0)

    gem5_verify_config(
        name='simple_gem5_returncode_test',

        # Pass our returncode verifier here.
        verifiers=(verifier,),

        # Use the pretend config file in the same directory as this test.
        config=joinpath(__directory__, 'simple-config.py'),
    )

We could then use the list command to look at the tests we have created.

.. code:: bash

    $ ./main.py list . --tests
    ==============================================================================================================
    Loading Tests

    Discovered 30 tests and 15 testsuites in /home/swilson/Projects/whimsy/docs/examples/simple_returncode_test.py
    ==============================================================================================================
    Listing all TestCases.
    ==============================================================================================================
    /home/swilson/Projects/whimsy/docs/examples:VerifyReturncode:simple_gem5_returncode_test [X86 - fast] (VerifyReturncode verifier)
    /home/swilson/Projects/whimsy/docs/examples:TestFunction:simple_gem5_returncode_test [RISCV - opt]
    /home/swilson/Projects/whimsy/docs/examples:VerifyReturncode:simple_gem5_returncode_test [RISCV - fast] (VerifyReturncode verifier)
    /home/swilson/Projects/whimsy/docs/examples:VerifyReturncode:simple_gem5_returncode_test [ALPHA - debug] (VerifyReturncode verifier)
    /home/swilson/Projects/whimsy/docs/examples:VerifyReturncode:simple_gem5_returncode_test [X86 - opt] (VerifyReturncode verifier)
    /home/swilson/Projects/whimsy/docs/examples:VerifyReturncode:simple_gem5_returncode_test [ARM - fast] (VerifyReturncode verifier)
    /home/swilson/Projects/whimsy/docs/examples:TestFunction:simple_gem5_returncode_test [RISCV - debug]
    /home/swilson/Projects/whimsy/docs/examples:TestFunction:simple_gem5_returncode_test [X86 - opt]
    /home/swilson/Projects/whimsy/docs/examples:TestFunction:simple_gem5_returncode_test [SPARC - fast]
    ... 21 More tests elided...

A less contrived example is to run gem5 using a config and a test
program. Here's an example of how to do this as well:

.. code:: python

    from testlib import *

    verifiers = (
            # Create a verifier that will check that the output 
            # contains the regex 'hello'
            verifier.MatchRegex('hello'),

            # The se.py script is dumb and sets a strange return code on success.
            verifier.VerifyReturncode(1),)
    hello_program = TestProgram('hello', 'X86', 'linux')

    gem5_verify_config(
        name='test_hello',

        # We now rely on the hello_program to be built before this test is run.
        fixtures=(hello_program,),
        verifiers=verifiers,

        # Use the se.py config from configs/example/se.py
        config=joinpath(config.base_dir, 'configs', 'example','se.py'),

        # Give the config the command and path.
        config_args=['--cmd', hello_program.path],

        # The hello_program only works on the X86 ISA.
        valid_isas=('X86',)
    )

The new additions to pick out from this example are:

-  We are handing a tuple of verifiers to ``gem5_verify_config``. We can
   provide any number of these.
-  We created a ``TestProgram`` - a fixture which will be ``setup``
   before our suite runs. We can also hand any number of these to
   ``gem5_verify_config``.
-  We can hand config arguments by passing and array of flags/args under
   the kwarg ``config_args``

Running Your Test
~~~~~~~~~~~~~~~~~

There are now a few ways to run this last suite we've just created.

First we could run every test in the directory it's stored in. Assuming
you file is stored in ``/tests/test-hello.py``. we would run it by
executing the command:

.. code:: bash

    ./main.py run /tests

If we only want to run this specific suite we need to run by giving the
uid:

.. code:: bash

    ./main.py run /tests --uid '/tests/test-hello:TestSuite:simple_gem5_returncode_test [X86 - opt]'

If we want to run all the tests with the X86 tag we could run it with
one of the tags that was automatically added by ``gem5_verify_config``:

.. code:: bash

    ./main.py run /tests --tags X86

Writing Your Own Test
---------------------

The ``gem5_verify_config`` method covers all the use cases of the old
testing framework as far as I know, however the major reason for
creating a new framework is so we have test cases that **actually test
something**. (It's of my opinion that the old tests are all but useless
and should be scrapped save for a couple for top level functional
testing.) As such, advanced users should be able to create their own
tests easily.

As a 'simple' example we'll duplicate some functionality of
``gem5_verify_config`` and create a test that manually spawns gem5 and
checks it's return code.

.. code:: python

    from testlib import *

    # Create a X86/gem5.opt target fixture.
    gem5 = Gem5Fixture(constants.x86_tag, constants.opt_tag)

    # Use the helper function wrapper which creates a TestCase out of this
    # function. The test will automatically get the name of this function. The
    # fixtures provided will automatically be given to us by the test runner as
    # a dictionary of the format fixture.name -> fixture
    @testfunction(fixtures=(gem5,), 
                  tags=[constants.x86_tag, constants.opt_tag])
    def test_gem5_returncode(fixtures):

        # Collect our gem5 fixture using the standard name and get the path of it.
        gem5 = fixtures[constants.gem5_binary_fixture_name].path

        command = [
            gem5,
            config=joinpath(config.base_dir, 'configs', 'example','se.py'),
        ]

        try: 
            # Run the given command sending it's output to our log at a low
            # priorirty verbosity level.
            log_call(command)
        except CalledProcessError as e:
            if e.returncode == 1:
                # We can fail by raising an exception
                raise e 

            elif e.returncode != 2:
                # We can also fail manually with the fail method.
                test.fail("Return code wasn't 2")

        # Returncode was 0
        # When we return this test will be marked as passed.

Since the test function was not placed into a test suite by us, when it
is collected by the ``TestLoader`` it will automatically be placed into
a ``TestSuite`` with the name of the module.

Writing Your Own Fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`whimsy.fixture.Fixture` objects are a major component in writing
modular and composable tests while reducing code reuse. There are quite a few
``Fixture`` classes built in, but they might not be sufficient.

We'll pretend we have a test that requires we create a very large empty
blob file so gem5 can use it as a disk. *(Is that even possible?)*.

.. code:: python

    from testlib import *
    import os

    class DiskGeneratorFixture(Fixture):
        def __init__(self, path, size, name):
            super(DiskGeneratorFixture, self).__init__(
                  name, 
                  # Don't build this at startup, wait until a test that uses this runs.
                  lazy_init=True, 
                  # If multiple test suites use this, don't rebuild this fixture each time.
                  build_once=True)

            self.path = path
            self.size = size

        def setup(self):
            # This method is called from the Runner when a TestCase that uses this
            # fixture is about to run.

            super(DisckGeneratorFixture, self).setup()

            # Create the file using the dd program.
            log_call(['dd', 'if=/dev/zero', 'of=%s' % self.path, 'count=%d' % self.size])

        def teardown(self):
            # This method is called after the test or suite that uses this fixture
            # is done running.

            # Remove the file.
            os.remove(self.path)