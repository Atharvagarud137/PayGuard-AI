from sqlalchemy import text


def test_runtime_database_role_has_no_schema_ownership_or_ddl_privileges(
        db_session,
):
    privileges = db_session.execute(
        text(
            """
            SELECT
                current_user AS runtime_role,
                has_schema_privilege(current_user, 'public', 'CREATE')
                    AS can_create_in_schema,
                has_table_privilege(current_user, 'public.cards', 'SELECT')
                    AS can_read_cards,
                has_table_privilege(current_user, 'public.cards', 'INSERT')
                    AS can_insert_cards,
                has_table_privilege(current_user, 'public.cards', 'UPDATE')
                    AS can_update_cards,
                has_table_privilege(current_user, 'public.cards', 'DELETE')
                    AS can_delete_cards,
                has_table_privilege(current_user, 'public.audit_events', 'SELECT')
                    AS can_read_audit,
                has_table_privilege(current_user, 'public.audit_events', 'INSERT')
                    AS can_insert_audit,
                has_table_privilege(current_user, 'public.audit_events', 'UPDATE')
                    AS can_update_audit,
                has_table_privilege(current_user, 'public.audit_events', 'DELETE')
                    AS can_delete_audit,
                has_table_privilege(current_user, 'public.audit_events', 'TRUNCATE')
                    AS can_truncate_audit,
                has_table_privilege(current_user, 'public.audit_events', 'TRIGGER')
                    AS can_manage_audit_triggers,
                (SELECT pg_get_userbyid(relowner) FROM pg_class
                 WHERE oid = 'public.cards'::regclass) AS cards_owner,
                (SELECT pg_get_userbyid(relowner) FROM pg_class
                 WHERE oid = 'public.audit_events'::regclass) AS audit_owner
            """
        )
    ).mappings().one()

    assert privileges["runtime_role"] not in {
        privileges["cards_owner"],
        privileges["audit_owner"],
    }
    assert privileges["can_create_in_schema"] is False
    assert privileges["can_read_cards"] is True
    assert privileges["can_insert_cards"] is True
    assert privileges["can_update_cards"] is True
    assert privileges["can_delete_cards"] is True
    assert privileges["can_read_audit"] is True
    assert privileges["can_insert_audit"] is True
    assert privileges["can_update_audit"] is False
    assert privileges["can_delete_audit"] is False
    assert privileges["can_truncate_audit"] is False
    assert privileges["can_manage_audit_triggers"] is False
