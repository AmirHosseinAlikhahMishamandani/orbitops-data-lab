import pytest

pytest.importorskip("airflow")

from dags.orbitops_telemetry_pipeline import orbitops_pipeline

pytestmark = pytest.mark.airflow


def test_orbitops_dag_has_small_explicit_task_graph() -> None:
    dag = orbitops_pipeline()

    assert dag.dag_id == "orbitops_telemetry_pipeline"
    assert set(dag.task_dict) == {"generate", "process", "summarize"}
    assert dag.task_dict["process"].upstream_task_ids == {"generate"}
    assert dag.task_dict["summarize"].upstream_task_ids == {"process"}
    assert dag.catchup is False
    assert dag.max_active_runs == 1
