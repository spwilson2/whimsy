'''
File which implements querying logic for metadata about loaded items.
'''

def list_fixtures(loader):
    for fixture in loader.fixtures:
        print fixture.name

def list_tests(loader):
    for test in loader.tests:
        print test.name

def list_suites(loader):
    for suite in loader.suites:
        print suite.name

def list_tags(loader):
    # Go through all suites and all testcases looking at their tags.
    tags = set()
    for item in loader.suite.iter_inorder():
        tags.update(item.tags)
    for tag in tags:
        print tag

def list_tests_with_tags(loader, tags):
    for tag in tags:
        print 'Tests marked with %s tag' % tag
        for test in loader.tag_index(tag):
            print test.name
