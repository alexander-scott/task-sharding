load("@rules_python//python:defs.bzl", "py_test")

def target_gen(name, total_targets, **kwargs):
    for i in range(0, total_targets):
        py_test(
            name = name + "_" + str(i),
            args = [str(i)],
            **kwargs
        )
