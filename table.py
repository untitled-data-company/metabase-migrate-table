from dataclasses import dataclass, field
from common import call_metabase_api, get_source_table
from typing import Dict, List


@dataclass
class Table:
    old: str
    new: str
    renamed_columns: Dict[str, str] = field(default_factory=dict)
    old_schema: str = ""
    old_table: str = ""
    old_id: int = 0
    new_schema: str = ""
    new_table: str = ""
    new_id: int = 0
    old_fields: str = ""
    new_fields: str = ""
    collect_all: bool = False
    card_ids: List[int] = field(init=False)
    dashboard_ids: List[int] = field(init=False)

    def __post_init__(self):
        self.old_schema, self.old_table = self.old.split(".")
        self.new_schema, self.new_table = self.new.split(".")
        self.old_id = get_id(self.old)
        self.new_id = get_id(self.new)
        self.old_fields = _get_table_fields(self.old_id)
        self.new_fields = _get_table_fields(self.new_id)

        if self.renamed_columns:
            for old_field_name, new_field_name in self.renamed_columns.items():
                self.new_fields[old_field_name] = self.new_fields[new_field_name]

        self.card_ids = self._get_associated_cards() if self.collect_all else []
        self.dashboard_ids = (
            self._get_associated_dashboards() if self.collect_all else []
        )

    def update_query(self, query: str) -> str:
        return query.replace(self.old, self.new)

    # def apply_renaming(self, old_field_name: str) -> str:
    #     if self.renamed_columns and old_field_name in self.renamed_columns:
    #         return self.renamed_columns[old_field_name]
    #     return old_field_name

    def _get_associated_cards(self) -> List[int]:
        data = call_metabase_api(query_endpoint="card/")

        card_ids_query = [
            item["id"]
            for item in data
            if get_source_table(item.get("dataset_query", {}).get("query", {}))
            == self.old_id
        ]

        card_ids_native = [
            item["id"]
            for item in data
            if item.get("dataset_query", {})
            .get("native", {})
            .get("query", "")
            .find(self.old)
            > -1
        ]

        card_ids = card_ids_query + card_ids_native
        card_ids.sort()
        return card_ids

    def _get_associated_dashboards(self) -> List[int]:

        dashboard_ids = []
        for card_id in self.card_ids:
            query_data = (
                """{"parameters":[{"type":"id","value":[\""""
                + str(card_id)
                + """"],"id":"81d22d7f","target":["dimension",["field",46192,{"base-type":"type/Integer","join-alias":"Content - Card Qualified"}]]}]}"""
            )
            data = call_metabase_api(
                query_endpoint="dashboard/535/dashcard/8155/card/6429/query",
                method="POST",
                data=query_data,
            )

            dashboard_ids = dashboard_ids + (
                [dashboard[1] for dashboard in data.get("data", {}).get("rows", [])]
                if data
                else []
            )

        dashboard_ids = list(set(dashboard_ids))
        dashboard_ids.sort()

        return dashboard_ids

    def is_field_in_old_table(self, field_id) -> bool:
        return field_id in self.old_fields.values()


def _get_tables():
    query_endpoint = f"table/"
    return call_metabase_api(query_endpoint)


def _get_table_fields(table_id):
    query_endpoint = f"table/{table_id}/query_metadata"
    fields = {
        field["name"]: field["id"]
        for field in call_metabase_api(query_endpoint)["fields"]
    }
    return fields


def get_id(table):
    table_list = _get_tables()
    return [x["id"] for x in table_list if f"{x['schema']}.{x['name']}" == table][0]
