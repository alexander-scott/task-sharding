from django.test import TestCase

from task_director.src.controller import TaskDirectorController

from task_director.test.mock_classes.mock_consumer import MockConsumer


class TaskDirectorTests__Setup(TestCase):
    def test__controller_initialisation(self):
        """
        Check that the controller can be initialised.
        """
        controller = TaskDirectorController()
        self.assertNotEqual(None, controller)

    def test__add_consumer_to_controller(self):
        controller = TaskDirectorController()
        created_consumer = MockConsumer("UUID1")

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(0, registered_consumers)

        controller.register_consumer("UUID1", created_consumer)

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(1, registered_consumers)

        controller.deregister_consumer("UUID1")

        registered_consumers = controller.get_total_registered_consumers()
        self.assertEqual(0, registered_consumers)
