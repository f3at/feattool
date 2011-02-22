import os

from twisted.spread import pb
from twisted.internet import defer
from twisted.python import failure

from feat.test import common
from feat.agencies.net import broker
from feat.common import log, manhole


class DummyAgency(log.LogProxy, manhole.Manhole):

    def __init__(self, testcase):
        log.LogProxy.__init__(self, testcase)

    @manhole.expose()
    def echo(self, text):
        return text


class BrokerTest(common.TestCase):

    timeout=3

    def setUp(self):
        self.brokers = [broker.Broker(DummyAgency(self)) for x in range(3)]
        self._delete_socket_file()

    @defer.inlineCallbacks
    def testInitiateMaster(self):
        for x in self.brokers:
            self.assert_role(x, broker.BrokerRole.disconnected)

        master = self.brokers[0]
        master.initiate_broker()
        self.assert_role(master, broker.BrokerRole.master)
        yield master.disconnect()
        self.assert_role(master, broker.BrokerRole.disconnected)

    @defer.inlineCallbacks
    def testInitiateMasterAndSlave(self):
        master = self.brokers[0]
        yield master.initiate_broker()
        slave = self.brokers[1]

        d = self.cb_after(None, master, 'append_slave')
        yield slave.initiate_broker()

        self.assert_role(master, broker.BrokerRole.master)
        self.assert_role(slave, broker.BrokerRole.slave)

        yield d
        self.assertEquals(1, len(master.slaves))
        self.assertEquals(1, len(master.factory.connections))

        result = yield master.slaves[0].callRemote('echo', "hello world!")
        self.assertEqual("hello world!", result)

    @defer.inlineCallbacks
    def testSlaveComesAndGoes(self):
        master = self.brokers[0]
        yield master.initiate_broker()
        slave = self.brokers[1]

        yield slave.initiate_broker()

        slave.disconnect()
        yield common.delay(None, 0.1)

        self.assertEquals(0, len(master.slaves))
        self.assertEquals(0, len(master.factory.connections))

    @defer.inlineCallbacks
    def testMasterGoesSlaveTakesOver(self):
        master = self.brokers[0]
        yield master.initiate_broker()
        slave = self.brokers[1]
        yield slave.initiate_broker()

        self.log('Disconnecting master')
        yield master.disconnect()
        yield slave.wait_for_state(broker.BrokerRole.master)
        self.assert_role(master, broker.BrokerRole.disconnected)
        self.assert_role(slave, broker.BrokerRole.master)

    @defer.inlineCallbacks
    def testStaleSocketFileExists(self):
        # touch file
        open(self.brokers[0].socket_path, 'w').close()
        master = self.brokers[0]
        yield master.initiate_broker()
        self.assert_role(master, broker.BrokerRole.master)
        yield master.disconnect()
        self.assert_role(master, broker.BrokerRole.disconnected)

    @defer.inlineCallbacks
    def testThreeBrokersMasterDisconnects(self):
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        self.assert_role(master, broker.BrokerRole.master)
        self.assertEqual(2, len(master.slaves))

        self.assert_role(slave1, broker.BrokerRole.slave)
        self.assert_role(slave2, broker.BrokerRole.slave)

        yield master.disconnect()
        yield common.delay(None, 0.2)
        new_master = [x for x in (slave1, slave2, )\
                      if x._cmp_state(broker.BrokerRole.master)][0]
        self.assertEqual(1, len(new_master.slaves))

        yield master.initiate_broker()
        self.assertEqual(2, len(new_master.slaves))
        self.assert_role(master, broker.BrokerRole.slave)

    @defer.inlineCallbacks
    def testPusingEventsSlaveToMaster(self):
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        d = master.wait_event('some', 'event')
        yield slave1.push_event('some', 'event')
        yield d

    @defer.inlineCallbacks
    def testPusingEventsMasterToSlaves(self):
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        d1 = slave1.wait_event('some', 'event')
        d2 = slave2.wait_event('some', 'event')
        yield self._wait_for_events_registered(master, 2, 'some', 'event')
        yield master.push_event('some', 'event')
        yield d1
        yield d2

    @defer.inlineCallbacks
    def testFailingEventsMasterToSlaves(self):
        fail = failure.Failure(RuntimeError('failed'))
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        d1 = slave1.wait_event('some', 'event')
        self.assertFailure(d1, Exception)
        yield self._wait_for_events_registered(master, 1, 'some', 'event')
        yield master.fail_event(fail, 'some', 'event')
        yield d1

    @defer.inlineCallbacks
    def testFailingEventsSlaveToMaster(self):
        fail = failure.Failure(RuntimeError('failed'))
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        d1 = master.wait_event('some', 'event')
        self.assertFailure(d1, Exception)
        yield self._wait_for_events_registered(master, 1, 'some', 'event')
        yield slave1.fail_event(fail, 'some', 'event')
        yield d1

    @defer.inlineCallbacks
    def _wait_for_events_registered(self, broker, num, *args):
        key = broker._event_key(*args)
        while len(broker._events.get(key, list())) < num:
            yield common.delay(None, 0.1)

    @defer.inlineCallbacks
    def testPusingEventsSlaveToSlave(self):
        master, slave1, slave2 = self.brokers
        for x in self.brokers:
            yield x.initiate_broker()
        d = slave1.wait_event('some', 'event')
        yield self._wait_for_events_registered(master, 1, 'some', 'event')
        yield slave2.push_event('some', 'event')
        yield d

    @defer.inlineCallbacks
    def tearDown(self):
        for x in self.brokers:
            if not x._cmp_state(broker.BrokerRole.disconnected):
                yield x.disconnect()
        self._delete_socket_file()

    def _delete_socket_file(self):
        try:
            os.unlink(self.brokers[0].socket_path)
        except OSError:
            pass

    def assert_role(self, broker, role):
        self.assertEqual(role, broker._get_machine_state())