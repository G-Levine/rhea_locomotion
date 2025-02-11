# -*- python -*-
#
# Copyright 2022 Stéphane Caron

load("//tools/lint:lint.bzl", "add_lint_tests")
load("@pip_upkie_locomotion//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "whole_body_controller",
    srcs = [
        "wheel_balancer.py",
        "whole_body_controller.py",
    ],
    deps = [
        "//observers/base_pitch",
        "//utils:clamp",
        "//utils:filters",
        requirement("gin-config"),
        requirement("robot_descriptions"),
    ],
)

py_binary(
    name = "pink_balancer",
    srcs = [
        "pink_balancer.py",
        "wheel_balancer.py",
        "whole_body_controller.py",
    ],
    main = "pink_balancer.py",
    data = [
        ":config",
    ] + select({
        "//:pi32_config": ["//spines:pi3hat"],
        "//:pi64_config": ["//spines:pi3hat"],
        "//conditions:default": [],
    }),
    deps = [
        "//utils:realtime",
        "//utils:spdlog",
        ":whole_body_controller",
        "@mpacklog//:python",
        requirement("gin-config"),
        requirement("loop_rate_limiters"),
        "@vulp//spine:python",
    ],
)

add_lint_tests(enable_clang_format_lint = True)
