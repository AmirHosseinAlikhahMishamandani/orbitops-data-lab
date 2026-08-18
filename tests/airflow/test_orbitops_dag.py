import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

pytest.importorskip("airflow")

pytestmark = pytest.mark.airflow


def _load_dag_module() -> ModuleType:
    """Load the deployed DAG file without treating the dags directory as a package."""
    dag_path = Path(__file__).parents[2] / "dags" / "orbitops_telemetry_pipeline.py"
    spec = importlib.util.spec_from_file_location("orbitops_telemetry_pipeline", dag_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Airflow DAG module from {dag_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_orbitops_dag_has_small_explicit_task_graph() -> None:
    module = _load_dag_module()
    dag = module.orbitops_pipeline()

    assert dag.dag_id == "orbitops_telemetry_pipeline"
    assert set(dag.task_dict) == {"generate", "process", "summarize"}
    assert dag.task_dict["process"].upstream_task_ids == {"generate"}
    assert dag.task_dict["summarize"].upstream_task_ids == {"process"}
    assert dag.catchup is False
    assert dag.max_active_runs == 1
