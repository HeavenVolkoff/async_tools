# Internal
import sys
import asyncio
import unittest

# External
import asynctest
from async_tools.all_tasks import all_tasks


@asynctest.strict
class AllTasksTestCase(asynctest.TestCase, unittest.TestCase):
    @unittest.skipUnless(sys.version_info >= (3, 7), "This test is only valid in Python >= 3.7")
    @asynctest.fail_on(unused_loop=False)
    def test_import_correctness(self):
        self.assertIs(all_tasks, asyncio.all_tasks)

    @unittest.skipUnless(sys.version_info <= (3, 6), "This test is only valid in Python <= 3.6")
    @asynctest.fail_on(unused_loop=False)
    def test_import_correctness(self):
        self.assertIs(all_tasks, asyncio.Task.all_tasks)
