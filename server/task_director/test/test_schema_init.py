import json

from channels.testing import ApplicationCommunicator, WebsocketCommunicator
from django.test import TestCase

from task_director.src.message_type import MessageType

from task_director.test.defaults import create_application
from task_director.test.utils import proxy_message_from_channel_to_communicator, prompt_response_from_communicator


def create_client_init_message_default(
    repo_state=None, patchset_complexity=False, cache_id="1", schema_id="1", total_steps=1
) -> dict:
    if not repo_state:
        repo_state = {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            }
        }
    return {
        "message_type": MessageType.INIT,
        "repo_state": repo_state,
        "patchset_complexity": {
            "complex": patchset_complexity,
        },
        "cache_id": cache_id,
        "schema_id": schema_id,
        "total_steps": total_steps,
    }


def create_client_init_message_default_with_custom_repo_state(
    repo_name="org/repo_1",
    base_ref="main",
    patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
    additional_patchsets=None,
    **kwargs
) -> dict:
    repo_state = {
        repo_name: {
            "base_ref": base_ref,
            "patchset": patchset,
        }
    }
    if additional_patchsets:
        repo_state[repo_name]["additional_patchsets"] = additional_patchsets
    return create_client_init_message_default(repo_state=repo_state, **kwargs)


param_list = [
    [
        "no_instances_connected",
        [],
        [],
    ],
    [
        "single_instance_connected",
        [create_client_init_message_default()],
        [[0]],
    ],
    [
        "two_instances_connected_with_identical_config",
        [create_client_init_message_default(), create_client_init_message_default()],
        [[0]],
    ],
    # Core config tests
    [
        "two_instances_connected_with_differing_cache_id",
        [
            create_client_init_message_default(cache_id="1"),
            create_client_init_message_default(cache_id="2"),
        ],
        [[0], [1]],
    ],
    [
        "two_instances_connected_with_differing_schema_id",
        [
            create_client_init_message_default(schema_id="1"),
            create_client_init_message_default(schema_id="2"),
        ],
        [[0], [1]],
    ],
    # Repo state tests
    [
        "two_instances_connected_with_differing_branch_names",
        [
            create_client_init_message_default_with_custom_repo_state(base_ref="master"),
            create_client_init_message_default_with_custom_repo_state(base_ref="main"),
        ],
        [[0], [1]],
    ],
    [
        "two_instances_connected_with_differing_repo_names",
        [
            create_client_init_message_default_with_custom_repo_state(repo_name="org/repo_1"),
            create_client_init_message_default_with_custom_repo_state(repo_name="org/repo_2"),
        ],
        [[0], [1]],
    ],
    [
        "two_instances_connected_with_differing_patchsets",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas"
            ),
        ],
        [[0], [1]],
    ],
    [
        "two_instances_connected_with_first_clients_patchset_present_in_second_clients_additional_patchsets_list",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"],
            ),
        ],
        [[0, 1]],
    ],
    [
        "two_instances_connected_with_first_clients_patchset_not_present_in_second_clients_additional_patchsets_list",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["234234eadf9uqhr9ueafbizdh923849efk99s8fg"],
            ),
        ],
        [[0], [1]],
    ],
    [
        "three_instances_connected_with_patchsets_present_across_all_instances",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"],
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="2f05517de6887b51439fc2f62b836f5647978327",
                additional_patchsets=[
                    "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    "29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                ],
            ),
        ],
        [[0, 1, 2]],
    ],
    # Patchset complexity tests
    [
        "two_instances_connected_with_first_clients_patchset_present_in_second_clients_additional_patchsets_list_but_the_second_patchset_is_complex",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"],
                patchset_complexity=True,
            ),
        ],
        [[0], [1]],
    ],
    [
        "three_instances_connected_with_patchsets_present_across_all_instances_but_the_middle_instance_is_complex",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"],
                patchset_complexity=True,
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="2f05517de6887b51439fc2f62b836f5647978327",
                additional_patchsets=[
                    "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    "29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                ],
            ),
        ],
        [[0], [1, 2]],
    ],
    [
        "three_instances_connected_with_patchsets_present_across_all_instances_but_the_last_instance_is_complex",
        [
            create_client_init_message_default_with_custom_repo_state(
                patchset="5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                additional_patchsets=["5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71"],
            ),
            create_client_init_message_default_with_custom_repo_state(
                patchset="2f05517de6887b51439fc2f62b836f5647978327",
                additional_patchsets=[
                    "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                    "29fb9sda8yfbd9138239e8qahd8iuia1932wfhas",
                ],
                patchset_complexity=True,
            ),
        ],
        [[0, 1], [2]],
    ],
]


class TaskDirectorTests__SchemaInstanceInitialisation(TestCase):
    async def test__schema_instance_count(self):
        for name, consumer_configs, expected_consumer_arrangement in param_list:
            with self.subTest(name):
                application = create_application()
                controller = ApplicationCommunicator(application, {"type": "channel", "channel": "controller"})

                consumers = []
                consumer_to_instance_map = {}
                for index, consumer_config in enumerate(consumer_configs):
                    consumer = WebsocketCommunicator(application, "/ws/api/1/" + str(index) + "/")
                    connected, _ = await consumer.connect()
                    self.assertTrue(connected)
                    consumers.append(consumer)

                    # Mock client send to consumer via the websocket communicator
                    await consumer.send_to(text_data=json.dumps(consumer_config))

                    # Proxy the message sent from consumer to the controller
                    await proxy_message_from_channel_to_communicator("controller", controller)

                    # Get the instance ID this consumer was assigned to
                    assigned_instance_id = await prompt_response_from_communicator(
                        controller,
                        "get.schema.instance.id.for.client.id.msg",
                        "schema_instance_id",
                        {"id": str(index)},
                    )
                    consumer_to_instance_map[index] = assigned_instance_id

                # Assert all consumers in each arrangement belong to the same instance
                for arrangement in expected_consumer_arrangement:
                    arrangement_instance_ids = []
                    for consumer in arrangement:
                        arrangement_instance_ids.append(consumer_to_instance_map[consumer])
                    self.assertTrue(all(x == arrangement_instance_ids[0] for x in arrangement_instance_ids))

                total_registered_consumers = await prompt_response_from_communicator(
                    controller, "get.total.registered.consumers.msg", "total_registered_consumers"
                )
                total_running_schema_instances = await prompt_response_from_communicator(
                    controller, "get.total.running.schema.instances.msg", "total_running_schema_instances"
                )

                self.assertEqual(len(expected_consumer_arrangement), total_running_schema_instances)
                self.assertEqual(len(consumer_configs), total_registered_consumers)

                for consumer in consumers:
                    await consumer.disconnect()
                    await proxy_message_from_channel_to_communicator("controller", controller)

                controller.stop()
