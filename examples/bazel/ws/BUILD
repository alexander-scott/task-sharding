load("//:gen.bzl", "target_gen")

target_gen(
    name = "test_my_script",
    srcs = ["test_my_script.py"],
    main = "test_my_script.py",
    total_targets = 10,
)

py_test(
    name = "test_my_script_with_dependency",
    srcs = ["test_my_script.py"],
    main = "test_my_script.py",
    deps = [
        "//:test_my_script_9",
    ],
)
