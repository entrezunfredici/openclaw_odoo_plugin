import unittest

from python.odoo_connector import (
    FULLY_REVERSIBLE,
    NOT_REVERSIBLE,
    PARTIALLY_REVERSIBLE,
    ReversibilityInfo,
    RollbackService,
    SnapshotStore,
)


class RollbackServiceExportsTest(unittest.TestCase):
    def test_public_constants_are_importable(self) -> None:
        self.assertEqual(FULLY_REVERSIBLE, "FULLY_REVERSIBLE")
        self.assertEqual(PARTIALLY_REVERSIBLE, "PARTIALLY_REVERSIBLE")
        self.assertEqual(NOT_REVERSIBLE, "NOT_REVERSIBLE")

    def test_reversibility_levels_use_public_constants(self) -> None:
        service = RollbackService(SnapshotStore())

        self.assertEqual(
            service.get_reversibility("create"),
            ReversibilityInfo(
                FULLY_REVERSIBLE,
                "A created record can be deleted, but rollback execution is not implemented yet.",
            ),
        )
        self.assertEqual(
            service.get_reversibility("write"),
            ReversibilityInfo(
                FULLY_REVERSIBLE,
                "Previous values are snapshotted, but rollback execution is not implemented yet.",
            ),
        )
        self.assertEqual(
            service.get_reversibility("delete"),
            ReversibilityInfo(
                NOT_REVERSIBLE,
                "Deleted records cannot be restored by this plugin.",
            ),
        )

    def test_attempt_rollback_returns_stubbed_response(self) -> None:
        store = SnapshotStore()
        snapshot = store.create(
            action_log_id="log-1",
            model="project.task",
            operation="write",
            record_ids=[12],
            state_before={"records": [{"id": 12, "name": "Before"}]},
        )
        service = RollbackService(store)

        result = service.attempt_rollback(snapshot, client=object())

        self.assertFalse(result["ok"])
        self.assertTrue(result["rollback_requested"])
        self.assertFalse(result["rollback_executed"])
        self.assertEqual(result["status"], "not_implemented")
        self.assertEqual(result["snapshot_id"], snapshot.id)
        self.assertEqual(result["record_ids"], [12])


if __name__ == "__main__":
    unittest.main()
