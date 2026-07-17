"""Submit a credit-scaled Azure ML sweep for the quantum controller.

Run this from Azure ML Studio VS Code after uploading/syncing the repository and
filling workspace values in environment variables or command arguments.
"""

from __future__ import annotations

import argparse

from azure.ai.ml import Input, MLClient, Output, command
from azure.ai.ml.sweep import Choice, MedianStoppingPolicy, Uniform
from azure.identity import DefaultAzureCredential


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit Azure ML controller sweep")
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--compute", required=True)
    parser.add_argument(
        "--data",
        required=True,
        help="Azure ML uri_file/uri_folder path to controller_training.csv or its folder",
    )
    parser.add_argument("--target", default="final_error_abs")
    parser.add_argument("--feature-set", default="pre_run")
    parser.add_argument("--experiment-name", default="quantum_controller_sweep")
    parser.add_argument("--max-total-trials", type=int, default=100)
    parser.add_argument("--max-concurrent-trials", type=int, default=10)
    args = parser.parse_args()

    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=args.subscription_id,
        resource_group_name=args.resource_group,
        workspace_name=args.workspace_name,
    )

    base_job = command(
        code=".",
        command=(
            "python -m ml.train_controller "
            "--data ${{inputs.training_data}} "
            f"--target {args.target} "
            f"--feature-set {args.feature_set} "
            "--model-dir ${{outputs.model_dir}} "
            "--n-estimators ${{inputs.n_estimators}} "
            "--max-depth ${{inputs.max_depth}} "
            "--min-samples-leaf ${{inputs.min_samples_leaf}} "
            "--registered-model-name quantum_controller_model"
        ),
        inputs={
            "training_data": Input(type="uri_file", path=args.data),
            "n_estimators": 300,
            "max_depth": 0,
            "min_samples_leaf": 1,
        },
        outputs={"model_dir": Output(type="uri_folder")},
        environment="AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
        compute=args.compute,
        experiment_name=args.experiment_name,
        display_name="quantum_controller_train",
    )

    sweep_job = base_job.sweep(
        sampling_algorithm="random",
        primary_metric="mae" if args.target != "converged" else "f1",
        goal="minimize" if args.target != "converged" else "maximize",
        search_space={
            "n_estimators": Choice([100, 300, 600, 1000]),
            "max_depth": Choice([0, 6, 12, 24]),
            "min_samples_leaf": Choice([1, 2, 4, 8]),
        },
    )
    sweep_job.set_limits(
        max_total_trials=args.max_total_trials,
        max_concurrent_trials=args.max_concurrent_trials,
        timeout=60 * 60 * 8,
    )
    sweep_job.early_termination = MedianStoppingPolicy(
        delay_evaluation=5,
        evaluation_interval=2,
    )

    returned = ml_client.jobs.create_or_update(sweep_job)
    print(returned.name)
    print(returned.studio_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
