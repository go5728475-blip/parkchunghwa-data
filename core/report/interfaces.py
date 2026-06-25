"""Report export interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.built_report import BuiltReport


class IReportExporter(ABC):
    """Port for exporting built reports to string formats."""

    @abstractmethod
    def export(self, report: BuiltReport) -> str:
        """Serialize a built report to the target format."""
