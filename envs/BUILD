# -*- python -*-
#
# Copyright 2022 Stéphane Caron

load("//tools/lint:lint.bzl", "add_lint_tests")
load("@pip_upkie_locomotion//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "upkie_wheels_env",
    srcs = [
        "upkie_wheels_env.py",
        "upkie_wheels_reward.py",
    ],
    data = [
        "spine.yaml",
    ],
    deps = [
        "@upkie_locomotion//observers/base_pitch",
        "@vulp//spine:python",
        requirement("gym"),
        requirement("pyyaml"),
    ],
)

py_library(
    name = "envs",
    srcs = [
        "__init__.py",
    ],
    deps = [
        ":upkie_wheels_env",
    ],
)

add_lint_tests(enable_clang_format_lint = True)
