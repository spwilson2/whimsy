See already generated html documentation at  https://spwilson2.github.io/whimsy-rtd/.

See a quick description of different files in `FILES.rst <whimsy/FILES.rst>`__

To generate html documentation checkout the docs branch and from docs/ run 'make html'
(We use a separate branch since we have to disable automatic argument parsing.)

git checkout docs
. develop.sh
make -C docs html
