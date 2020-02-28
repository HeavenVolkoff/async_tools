# Internal
import unittest
from typing import NamedTuple
from unittest.mock import Mock

# External
import asynctest
from async_tools.emitter import Emitter


@asynctest.strict
class EmitterTestCase(asynctest.TestCase, unittest.TestCase):
    @asynctest.fail_on(unused_loop=False)
    def test_emit(self):
        """Basic synchronous emission works"""

        ee = Emitter()
        listener = Mock()

        class Event(NamedTuple):
            data: str

        ee.on(Event, listener)

        event = Event("Wowow")

        ee.emit(event)

        listener.assert_called_once_with(event)
