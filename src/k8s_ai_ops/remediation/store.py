from k8s_ai_ops.models.incident_record import (
    IncidentRecord,
)


class IncidentStore:
    """
    In-memory incident store.

    This gives us a persistence abstraction without coupling
    the remediation workflow to a database.

    Replace this implementation with Postgres/Redis/etc.
    later without changing the API or remediation service.
    """

    def __init__(self):
        self._records: dict[str, IncidentRecord] = {}

    def create(
        self,
        record: IncidentRecord,
    ) -> IncidentRecord:

        self._records[record.id] = record

        return record

    def get(
        self,
        incident_id: str,
    ) -> IncidentRecord | None:

        return self._records.get(
            incident_id
        )

    def update(
        self,
        record: IncidentRecord,
    ) -> IncidentRecord:

        record.update_timestamp()

        self._records[record.id] = record

        return record

    def delete(
        self,
        incident_id: str,
    ) -> None:

        self._records.pop(
            incident_id,
            None,
        )

    def list(self) -> list[IncidentRecord]:

        return list(
            self._records.values()
        )