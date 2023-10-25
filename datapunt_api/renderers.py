from typing import Any

from rest_framework_csv.renderers import CSVRenderer


class PaginatedCSVRenderer(CSVRenderer):
    results_field: str = 'results'

    def render(
            self,
            data: dict | list,
            media_type: str | None = None,
            renderer_context: dict[str, Any] = {},
            writer_opts: dict[str, Any] | None = None,
    ) -> str | bytes:
        if not isinstance(data, list):
            data = data.get(self.results_field, [])

        return super(PaginatedCSVRenderer, self).render(data, media_type, renderer_context, writer_opts)
