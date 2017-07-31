from whimsy import *

verifier = verifier.VerifyReturncode(0)

gem5_verify_config(
    name='simple_gem5_returncode_test',

    # Pass our returncode verifier here.
    verifiers=(verifier,),
    # Use the pretend config file in the same directory as this test.
    config=joinpath(__directory__, 'simple-config.py'),
    config_args=None
)
