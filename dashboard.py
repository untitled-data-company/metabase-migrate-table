from dataclasses import dataclass, field

from common import call_metabase_api, get_source_table, modify_field_values
from table import Table


@dataclass
class Dashboard:
    id: int
    data: str = ""
    card_ids: list[int] = field(init=False)

    def _get_dashboard(self):
        query_endpoint = f"dashboard/{self.id}"
        return call_metabase_api(query_endpoint)

    def _get_associated_cards(self):

        return [
            dashcard["card"]["id"]
            for dashcard in self.data["dashcards"]
            if "virtual_card" not in dashcard["visualization_settings"]
        ]

    def __post_init__(self):
        self.data = self._get_dashboard()
        if self.data:
            self.card_ids = self._get_associated_cards()

    def save(self):
        query_endpoint = f"dashboard/{self.id}"
        return call_metabase_api(query_endpoint, method="PUT", data=self.data)

    def update_parameters(self, table: Table):
        """
        This method parses the dashcards in a dashboard and replace the field references
        """

        new_dashcards = []
        for dashcard in self.data["dashcards"]:
            if "virtual_card" not in dashcard["visualization_settings"]:
                card = dashcard["card"]
                if card["query_type"] == "native":
                    if card["dataset_query"]["native"]["query"].find(table.old) > -1:
                        dashcard["parameter_mappings"] = modify_field_values(
                            dashcard["parameter_mappings"], table
                        )
                        print(
                            f"   dashcard {dashcard["id"]} pointing to {card["id"]}: updated parameter_mappings"
                        )
                    else:
                        print(
                            f"   dashcard {dashcard["id"]} pointing to {card["id"]}: no changes needed"
                        )

                if card["query_type"] == "query":
                    if get_source_table(card["dataset_query"]["query"]) == table.old_id:
                        dashcard["parameter_mappings"] = modify_field_values(
                            dashcard["parameter_mappings"], table
                        )
                        print(
                            f"   dashcard {dashcard["id"]} pointing to {card["id"]}: updated parameter_mappings"
                        )
                    else:
                        print(
                            f"   dashcard {dashcard["id"]} pointing to {card["id"]}: no changes needed"
                        )

            new_dashcards.append(dashcard)

        self.data["dashcards"] = new_dashcards
