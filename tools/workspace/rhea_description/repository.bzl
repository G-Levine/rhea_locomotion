# -*- python -*-
#
# Copyright 2022 Stéphane Caron

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

def rhea_description_repository():
    """
    Clone repository from GitHub and make its targets available for binding.
    """
    git_repository(
        name = "rhea_description",
        remote = "https://github.com/G-Levine/rhea_description",
        commit = "72727c11086514bc08f55e0c133f7e8f997bd4ec",
        shallow_since = "1652897584 +0200"
    )
