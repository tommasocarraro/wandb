from wandb.cli import cli
from wandb.sdk.internal.internal_api import Api as InternalApi

import pytest
import wandb


@pytest.fixture()
def launch_queue(api=None):
    """
    Create a fixture that creates a launch queue, required for
    all launch `--queue` tests

    TODO: How to pass the username into this function? randomly generated
       so it must be passed in...
    """
    pass


@pytest.mark.timeout(300)
def test_launch_build_push_job(relay_server, runner, user, monkeypatch):
    # create a project
    PROJ = "test_project_1"
    monkeypatch.setenv("WANDB_PROJECT", PROJ)
    run = wandb.init(project=PROJ)
    # create a queue in the project
    api = InternalApi()
    api.create_run_queue(
        entity=user, project=PROJ, queue_name="queue", access="PROJECT"
    )

    args = [
        "https://github.com/gtarpenning/wandb-launch-test",
        f"--project={PROJ}",
        f"--entity={user}",
        "--job=oops",
        "--queue=queue",
        "--build",
    ]
    with relay_server() as relay:
        result = runner.invoke(cli.launch, args)
        print(relay.context.raw_data)

    run.finish()  # weird file sync error if run ends too early

    assert result.exit_code == 0
    assert "'uri': None" in str(result.output)
    assert "'job': 'oops'" not in str(result.output)
