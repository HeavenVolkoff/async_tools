# Internal
import sys
import asyncio
import unittest

# External
import asynctest

# External
from async_tools.current_task import current_task


@asynctest.strict
class CurrentTaskTestCase(asynctest.TestCase, unittest.TestCase):
    @unittest.skipUnless(sys.version_info >= (3, 7), "This test is only valid in Python >= 3.7")
    @asynctest.fail_on(unused_loop=False)
    def test_import_correctness(self):
        self.assertIs(current_task, asyncio.current_task)

    @unittest.skipUnless(sys.version_info <= (3, 6), "This test is only valid in Python <= 3.6")
    @asynctest.fail_on(unused_loop=False)
    def test_import_correctness(self):
        self.assertIs(current_task, asyncio.Task.current_task)
