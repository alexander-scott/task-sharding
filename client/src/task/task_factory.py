from src.task.sleep_task import SleepTask


def get_class_by_name(classname):
    cls = globals()[classname]
    return cls()
