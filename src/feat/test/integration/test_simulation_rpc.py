from twisted.internet import defer
from twisted.python import failure

from feat.test.integration import common

from feat.agents.base import agent, descriptor, replay
from feat.agents.common import rpc
from feat.common.text_helper import format_block

from feat.interface.recipient import *


@descriptor.register("rpc_test_agent")
class Descriptor(descriptor.Descriptor):
    pass


@agent.register("rpc_test_agent")
class Agent(agent.BaseAgent, rpc.AgentMixin):

    @replay.mutable
    def initiate(self, state):
        agent.BaseAgent.initiate(self)
        rpc.AgentMixin.initiate(self)
        state.value = None

    @replay.immutable
    def get_value(self, state):
        return state.value

    @rpc.publish
    @replay.mutable
    def set_value(self, state, value):
        result, state.value = state.value, value
        return result

    @rpc.publish
    def raise_error(self, Klass):
        raise Klass()

    @rpc.publish
    def return_failure(self, Klass):
        try:
            raise Klass()
        except:
            return failure.Failure()

    def not_published(self):
        pass


class RPCTest(common.SimulationTest):

    def prolog(self):
        setup = format_block("""
        agency = spawn_agency()
        desc1 = descriptor_factory('rpc_test_agent')
        desc2 = descriptor_factory('rpc_test_agent')
        m1 = agency.start_agent(desc1)
        m2 = agency.start_agent(desc2)
        agent1 = m1.get_agent()
        agent2 = m2.get_agent()
        """)
        return self.process(setup)

    def testValidateProlog(self):
        agents = [x for x in self.driver.iter_agents()]
        self.assertEqual(2, len(agents))

    @defer.inlineCallbacks
    def testCallRemote(self):
        agent1 = self.get_local('agent1')
        agent2 = self.get_local('agent2')
        recip1 = IRecipient(agent1)
        recip2 = IRecipient(agent2)

        self.assertEqual(agent1.get_value(), None)
        self.assertEqual(agent2.get_value(), None)

        result = yield agent1.callRemote(recip2, "set_value", "spam")

        self.assertEqual(result, None)
        self.assertEqual(agent1.get_value(), None)
        self.assertEqual(agent2.get_value(), "spam")

        result = yield agent1.callRemote(recip2, "set_value", "bacon")

        self.assertEqual(result, "spam")
        self.assertEqual(agent1.get_value(), None)
        self.assertEqual(agent2.get_value(), "bacon")

        result = yield agent2.callRemote(recip1, "set_value", "eggs")

        self.assertEqual(result, None)
        self.assertEqual(agent1.get_value(), "eggs")
        self.assertEqual(agent2.get_value(), "bacon")

        result = yield agent2.callRemote(recip1, "set_value", "beans")

        self.assertEqual(result, "eggs")
        self.assertEqual(agent1.get_value(), "beans")
        self.assertEqual(agent2.get_value(), "bacon")

        # Calling on itself

        result = yield agent2.callRemote(recip2, "set_value", "ham")

        self.assertEqual(result, "bacon")
        self.assertEqual(agent1.get_value(), "beans")
        self.assertEqual(agent2.get_value(), "ham")

        result = yield agent1.callRemote(recip1, "set_value", "tomatoes")

        self.assertEqual(result, "beans")
        self.assertEqual(agent1.get_value(), "tomatoes")
        self.assertEqual(agent2.get_value(), "ham")

    def testRemoteError(self):
        agent1 = self.get_local('agent1')
        agent2 = self.get_local('agent2')
        recip1 = IRecipient(agent1)
        recip2 = IRecipient(agent2)

        self.assertEqual(agent1.get_value(), None)
        self.assertEqual(agent2.get_value(), None)

        d = defer.succeed(None)

        d = self.assertAsyncFailure(d, (ValueError, ), agent1.callRemote,
                                    recip2, "raise_error", ValueError)

        d = self.assertAsyncFailure(d, (TypeError, ), agent1.callRemote,
                                    recip2, "return_failure", TypeError)

        d = self.assertAsyncFailure(d, (ValueError, ), agent2.callRemote,
                                    recip1, "raise_error", ValueError)

        d = self.assertAsyncFailure(d, (TypeError, ), agent2.callRemote,
                                    recip1, "return_failure", TypeError)

        d = self.assertAsyncFailure(d, (ValueError, ), agent1.callRemote,
                                    recip1, "raise_error", ValueError)

        d = self.assertAsyncFailure(d, (TypeError, ), agent1.callRemote,
                                    recip1, "return_failure", TypeError)

        return d

    def testNotPublished(self):
        agent1 = self.get_local('agent1')
        agent2 = self.get_local('agent2')
        recip1 = IRecipient(agent1)
        recip2 = IRecipient(agent2)

        self.assertEqual(agent1.get_value(), None)
        self.assertEqual(agent2.get_value(), None)

        d = defer.succeed(None)

        d = self.assertAsyncFailure(d, (rpc.NotPublishedError, ),
                                    agent1.callRemote, recip2, "not_published")

        d = self.assertAsyncFailure(d, (rpc.NotPublishedError, ),
                                    agent2.callRemote, recip1, "not_published")

        d = self.assertAsyncFailure(d, (rpc.NotPublishedError, ),
                                    agent1.callRemote, recip1, "not_published")

        return d