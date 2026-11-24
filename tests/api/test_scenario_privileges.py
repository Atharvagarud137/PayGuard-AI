from sqlalchemy import text


def test_runtime_scenario_storage_privileges_are_restricted(db_session):
    privileges = db_session.execute(text("""
        SELECT
            has_table_privilege(current_user, 'public.scenario_definitions', 'SELECT') AS definitions_read,
            has_table_privilege(current_user, 'public.scenario_definitions', 'INSERT') AS definitions_insert,
            has_table_privilege(current_user, 'public.scenario_definitions', 'UPDATE') AS definitions_update,
            has_table_privilege(current_user, 'public.scenario_definitions', 'DELETE') AS definitions_delete,
            has_table_privilege(current_user, 'public.scenario_runs', 'SELECT') AS runs_read,
            has_table_privilege(current_user, 'public.scenario_runs', 'INSERT') AS runs_insert,
            has_table_privilege(current_user, 'public.scenario_runs', 'UPDATE') AS runs_table_update,
            has_table_privilege(current_user, 'public.scenario_runs', 'DELETE') AS runs_delete,
            has_column_privilege(current_user, 'public.scenario_runs', 'status', 'UPDATE') AS runs_status_update,
            has_column_privilege(current_user, 'public.scenario_runs', 'snapshot_json', 'UPDATE') AS runs_snapshot_update
    """)).mappings().one()
    assert privileges["definitions_read"] is True
    assert privileges["definitions_insert"] is True
    assert privileges["definitions_update"] is False
    assert privileges["definitions_delete"] is False
    assert privileges["runs_read"] is True
    assert privileges["runs_insert"] is True
    assert privileges["runs_table_update"] is False
    assert privileges["runs_delete"] is False
    assert privileges["runs_status_update"] is True
    assert privileges["runs_snapshot_update"] is False
