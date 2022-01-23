import json

from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from django.test import TestCase

from task_sharding.test.defaults import (
    create_application,
    create_default_client_init_message,
    create_default_build_instruction_message,
    create_default_task_complete_message,
    create_default_schema_complete_message,
)
from task_sharding.test.utils import (
    proxy_message_from_channel_to_communicator,
    send_message_between_communicators,
)


class TaskShardingTests__SingleConsumerTaskComplete(TestCase):
    async def setUpAsync(self):
        application = create_application()
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer.connect()

    async def tearDownAsync(self):
        await self.consumer.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)

    async def test__when_one_consumer_connected__and_single_schema_task_is_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN a consumer connects and sends an INIT message with a single task,
          AND the server sends a build instruction message to the consumer,
          AND the consumer subsequently sends a successful task complete message.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message()
        await send_message_between_communicators(self.consumer, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_msg = create_default_build_instruction_message()
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_msg, json.loads(actual_build_instruction_msg))

        # Send task complete message to controller
        client_task_complete_msg = create_default_task_complete_message()
        await send_message_between_communicators(self.consumer, self.controller, client_task_complete_msg)

        # Assert the controller sent the correct schema complete message to the consumer
        expected_schema_complete_msg = create_default_schema_complete_message()
        actual_schema_complete_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()

    async def test__when_one_consumer_connected__and_multi_task_schema_is_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN a consumer connects and sends an INIT message with multiple tasks,
          AND the consumer subsequently sends multiple successful task complete messages.
        EXPECT the server to return to the same consumer a schema complete message.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message(2)
        await send_message_between_communicators(self.consumer, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_1_msg = create_default_build_instruction_message("1")
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_1_msg, json.loads(actual_build_instruction_msg))

        # Send client task complete message to controller
        client_task_1_complete_msg = create_default_task_complete_message("1")
        await send_message_between_communicators(self.consumer, self.controller, client_task_1_complete_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_build_instruction_2_msg = create_default_build_instruction_message("0")
        actual_build_instruction_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_build_instruction_2_msg, json.loads(actual_build_instruction_msg))

        # Send client task complete message to controller
        client_task_2_complete_msg = create_default_task_complete_message("0")
        await send_message_between_communicators(self.consumer, self.controller, client_task_2_complete_msg)

        # Assert the controller sent the correct schema complete message to the consumer
        expected_schema_complete_msg = create_default_schema_complete_message()
        actual_schema_complete_msg = await self.consumer.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()


class TaskShardingTests__TwoConsumersTaskComplete(TestCase):
    async def setUpAsync(self):
        application = create_application()
        self.controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})
        self.consumer1 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer1.connect()
        self.consumer2 = WebsocketCommunicator(application, "/ws/api/1/1/")
        await self.consumer2.connect()

    async def tearDownAsync(self):
        await self.consumer1.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)
        await self.consumer2.disconnect()
        await proxy_message_from_channel_to_communicator("controller", self.controller)

    async def test__when_two_consumers_connected__and_both_schema_tasks_are_successful__expect_schema_complete_msg_sent(
        self,
    ):
        """
        GIVEN a freshly instantiated TaskShardingController.
        WHEN two consumers connect and send an INIT message with the same config and two tasks,
          AND the server sends a different build instruction message to each consumer,
          AND the consumers subsequently send a successful task complete message.
        EXPECT the server to return to both consumers a schema complete message.
        """

        await self.setUpAsync()

        # Send client init message to controller
        client_init_msg = create_default_client_init_message(2)
        await send_message_between_communicators(self.consumer1, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_client_1_build_instruction_msg = create_default_build_instruction_message("1")
        actual_build_instruction_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_client_1_build_instruction_msg, json.loads(actual_build_instruction_msg))

        # Send client init message to controller
        await send_message_between_communicators(self.consumer2, self.controller, client_init_msg)

        # Assert the controller sent the correct build instruction to the consumer
        expected_client_2_build_instruction_msg = create_default_build_instruction_message("0")
        actual_build_instruction_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_client_2_build_instruction_msg, json.loads(actual_build_instruction_msg))

        # Send client task complete message to controller
        client_1_task_complete_msg = create_default_task_complete_message("0")
        await send_message_between_communicators(self.consumer1, self.controller, client_1_task_complete_msg)

        # Send client task complete message to controller
        client_2_task_complete_msg = create_default_task_complete_message("1")
        await send_message_between_communicators(self.consumer2, self.controller, client_2_task_complete_msg)

        # Assert the controller sent the correct schema complete message to the consumer
        expected_schema_complete_msg = create_default_schema_complete_message()
        actual_schema_complete_msg = await self.consumer1.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))
        actual_schema_complete_msg = await self.consumer2.receive_from()
        self.assertDictEqual(expected_schema_complete_msg, json.loads(actual_schema_complete_msg))

        await self.tearDownAsync()
