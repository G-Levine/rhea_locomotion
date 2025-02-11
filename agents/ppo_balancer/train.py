#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2023 Inria

import argparse
import json
import os
import random
import signal
import time
from typing import List

import gin
import stable_baselines3
from gym.wrappers.time_limit import TimeLimit
from rules_python.python.runfiles import runfiles
from settings import Settings
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.logger import TensorBoardOutputFormat
from torch import nn

from upkie_locomotion.envs import UpkieWheelsEnv
from upkie_locomotion.utils.spdlog import logging


class SummaryWriterCallback(BaseCallback):
    def __init__(self, env: UpkieWheelsEnv):
        super().__init__()
        self.config = env.config
        self.env = env

    def _on_training_start(self):
        output_formats = self.logger.output_formats
        self.tb_formatter = next(
            formatter
            for formatter in output_formats
            if isinstance(formatter, TensorBoardOutputFormat)
        )
        self.tb_formatter.writer.add_text(
            "env_id",
            self.env.id(),
            global_step=None,
        )
        self.tb_formatter.writer.add_text(
            "spine_config",
            f"```json\n{json.dumps(self.config, indent=4)}\n```",
            global_step=None,
        )

    def _on_step(self) -> bool:
        if self.n_calls == 1:
            # Wait for first call to log operative config so that parameters
            # for functions called by the environment are logged as well.
            self.tb_formatter.writer.add_text(
                "gin_config",
                f"```\n{gin.operative_config_str()}\n```",
                global_step=None,
            )


def train_policy(
    agent_name: str,
    training_dir: str,
    max_episode_duration: float = 10.0,
) -> None:
    """
    Train a new policy and save it to a directory.

    Args:
        agent_name: Agent name.
        training_dir: Directory for logging and saving policies.
        max_episode_duration: Maximum episode duration in seconds.
    """
    settings = Settings()
    brain_frequency = settings.brain_frequency
    policy_kwargs = {
        "activation_fn": nn.Tanh,
        "net_arch": [dict(pi=[64, 64], vf=[64, 64])],
    }
    env = TimeLimit(
        UpkieWheelsEnv(shm_name=f"/{agent_name}"),
        max_episode_steps=int(max_episode_duration * brain_frequency),
    )

    # Open threads:
    #
    # - policy initialization
    # - faster training by adding base angular velocity
    # - cost function: penalize velocity, distance to target

    dt = 1.0 / brain_frequency
    gamma = 1.0 - dt / settings.effective_time_horizon
    policy = stable_baselines3.PPO(
        "MlpPolicy",
        env,
        learning_rate=settings.learning_rate,
        n_steps=settings.n_steps,
        batch_size=settings.batch_size,
        n_epochs=settings.n_epochs,
        gamma=gamma,
        gae_lambda=settings.gae_lambda,
        clip_range=settings.clip_range,
        clip_range_vf=settings.clip_range_vf,
        normalize_advantage=True,
        ent_coef=settings.ent_coef,
        vf_coef=settings.vf_coef,
        max_grad_norm=settings.max_grad_norm,
        use_sde=settings.use_sde,
        sde_sample_freq=settings.sde_sample_freq,
        target_kl=settings.target_kl,
        tensorboard_log=training_dir,
        policy_kwargs=policy_kwargs,
        verbose=1,
    )

    tb_log_name = f"{agent_name}_env-v{env.version}"
    try:
        policy.learn(
            total_timesteps=settings.total_timesteps,
            callback=[
                CheckpointCallback(
                    save_freq=int(1e5),
                    save_path=f"{training_dir}/{tb_log_name}_1",
                    name_prefix="checkpoint",
                ),
                SummaryWriterCallback(env),
            ],
            tb_log_name=tb_log_name,
        )
    except KeyboardInterrupt:
        logging.info("Training interrupted.")

    # Save policy no matter what!
    policy.save(f"{training_dir}/{agent_name}")
    policy.env.close()


def generate_agent_name():
    with open("/usr/share/dict/words") as fh:
        words = fh.read().splitlines()
    word_index = random.randint(0, len(words))
    while not words[word_index].isalnum():
        word_index = (word_index + 1) % len(words)
    return words[word_index]


def get_bullet_argv(agent_name: str, show: bool) -> List[str]:
    """
    Get command-line arguments for the Bullet spine.

    Args:
        agent_name: Agent name.
        show: If true, show simulator GUI.

    Returns:
        Command-line arguments.
    """
    settings = Settings()
    brain_frequency = settings.spine_frequency
    spine_frequency = settings.spine_frequency
    assert spine_frequency % brain_frequency == 0
    nb_substeps = spine_frequency / brain_frequency
    bullet_argv = []
    bullet_argv.extend(["--shm-name", f"/{agent_name}"])
    bullet_argv.extend(["--nb-substeps", str(nb_substeps)])
    bullet_argv.extend(["--spine-frequency", str(spine_frequency)])
    if show:
        bullet_argv.append("--show")
    return bullet_argv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show",
        default=False,
        action="store_true",
        help="show simulator during trajectory rollouts",
    )
    parser.add_argument(
        "--wait",
        help="duration to wait for the spine to start",
        type=float,
        default=2.0,
    )
    args = parser.parse_args()

    agent_dir = os.path.dirname(__file__)
    gin.parse_config_file(f"{agent_dir}/settings.gin")

    agent_name = generate_agent_name()
    logging.info('New agent name is "%s"', agent_name)
    pid = os.fork()
    if pid == 0:  # child process: spine
        deez_runfiles = runfiles.Create()
        spine_path = os.path.join(
            agent_dir,
            deez_runfiles.Rlocation("upkie_locomotion/spines/bullet"),
        )
        argv = get_bullet_argv(agent_name, show=args.show)
        os.execvp(spine_path, ["bullet"] + argv)
    else:  # parent process: trainer
        wait_duration = args.wait  # [s]
        logging.info("Waiting %s s for simulator to spawn...", wait_duration)
        logging.info("You can adapt this duration to your machine with --wait")
        time.sleep(wait_duration)
        try:
            training_dir = f"{agent_dir}/policies"
            logging.info("Logging to %s", training_dir)
            logging.info(
                "To track in TensorBoard:\n\n\t"
                f"tensorboard --logdir {training_dir}"
                "\n\n"
            )
            train_policy(agent_name, training_dir)
        finally:
            os.kill(pid, signal.SIGINT)  # interrupt spine child process
            os.waitpid(pid, 0)  # wait for spine to terminate
