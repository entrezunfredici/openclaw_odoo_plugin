import unittest

from python.odoo_connector import (
    FULLY_REVERSIBLE,
    NOT_REVERSIBLE,
    PARTIALLY_REVERSIBLE,
    RollbackService,
    SnapshotStore,
)
from python.odoo_connector.rollback_service import ReversibilityInfo


class RollbackServiceExportsTest(unittest.TestCase):
    def test_public_constants_are_importable(self) -> None:
        self.assertEqual(FULLY_REVERSIBLE, "FULLY_REVERSIBLE")
        self.assertEqual(PARTIALLY_REVERSIBLE, "PARTIALLY_REVERSIBLE")
        self.assertEqual(NOT_REVERSIBLE, "NOT_REVERSIBLE")

    def test_reversibility_levels_use_public_constants(self) -> None:
        service = RollbackService(SnapshotStore())

        self.assertEqual(service.get_reversibility("create"), ReversibilityInfo(FULLY_REVERSIBLE, "Record can be deleted to undo the create."))
        self.assertEqual(service.get_reversibility("write"), ReversibilityInfo(FULLY_REVERSIBLE, "Previous values were snapshotted and can be restored."))
        self.assertEqual(service.get_reversibility("delete"), ReversibilityInfo(NOT_REVERSIBLE, "Deleted records cannot be recovered via this plugin."))


if __name__ == "__main__":
    unittest.main()
