
Migrating an Existing Test
--------------------------

Migrating an old test to whimsy takes a minor amount of work. We can use the
same :func:`whimsy.gem5.suite.gem5_verify_config` function and
:class:`whimsy.gem5.verifier.Verifier` subclasses we used to create our own
tests. Optionally we could add an additional utility function to make this even
easier, but I would prefer we keep consistency and not port many of the legacy
tests, since most legacy tests serve limited utility.

As an example we'll migrate the old
`quick/se/00.hello/arm/linux/simple-atomic-dummychecker` test. We'll refer to
the gem5 root directory as simply ``/``. That is, the old and new tests
directory would be ``/tests``.

Here are the steps:

1. Look in the directory the old test expects a ``test.py`` file to be located in.
2. Move that file and copy it into our new test location
   ``/tests/quick/se/00.hello`` and name the file ``config.py``. (Note that
   this is the same directory it was in originally.)
3. Move the reference files will not change location
   (``/tests/quick/se/00.hello/ref/arm/linux/simple-atomic-dummychecker``)
4. Assuming that the additional config files which set up the old test are not
   ported, we need to do so.

    - To do this copy over the old config to
      ``/tests/legacy-configs/simple-atomic-dummychecker.py`` (We know this is
      the legacy config name because it is the final name of the old test
      path.)

5. Create a ``test-hello.py`` file in this directory now, and use the
   gem5_verify_config and verifiers to match the golden standards.

.. code:: python

    from testlib import *


    verifiers = (
            verifier.MatchStdout(joinpath(__directory__, 'simout')),
            verifier.MatchStderr(joinpath(__directory__, 'simerr')),
            verifier.MatchStats(joinpath(__directory__, 'stat.txt')),
            verifier.VerifyReturncode(1),
            )

    # The test program still fits, only the path is changed from 'arm' to 'ARM'
    hello_program = TestProgram('hello', 'ARM', 'linux')

    # This is the path of legacy-configs that share the same base config.
    dummychecker =joinpath(config.base_dir,
    'tests',
    'legacy-configs',
    'simple-atomic-dummychecker.py')

    gem5_verify_config(
        name='test_hello',
        fixtures=(hello_program,),
        verifiers=verifiers,

        # All legacy configs rely on using the run.py script. It has been slightly
        # updated to make it more generic with less assumptions.
        config=joinpath(config.base_dir, 'tests', 'legacy-configs', 'run.py'),

        # Notice that the legacy run.py arguments have changed. It now forces users
        # to specify config files exactly rather than making assumptions on path.
        config_args=['--executable', hello_program.path,
            '--config', dummychecker,
            '--config', joinpath(getcwd(), 'config.py')],
        valid_isas=('ARM',)
    )
