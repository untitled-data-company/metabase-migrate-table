import argparse
import json
import sys
from typing import List

from card import Card
from dashboard import Dashboard
from table import Table
from common import BASE_URL


def replace_table_in_cards(card_ids: List[int], table: Table):
    for card_id in card_ids:

        print(f"** START - Processing Card {card_id} **")
        print(f"   card accessible at {BASE_URL}/question/{card_id}")

        c = Card(card_id)
        updates_flag = c.update_references(table)

        if not updates_flag:
            print(f"!! card {card_id} skipped because not using the provided table !!")
        c.save()

        print(f"** END - Processing Card {card_id} **")


def replace_table_in_dashboards(dashboard_ids: List[int], table: Table) -> None:
    """
    This method takes care of replacing the table references in a list of dashboards.
    """

    print(f"** START - Reading Dashboards info **")

    dashboards_info = [Dashboard(dashboard_id) for dashboard_id in dashboard_ids]

    print(f"** END - Reading Dashboards info **")

    for d in dashboards_info:
        dashboard_id = d.id

        print(f"** START - Processing Dashboard {dashboard_id} **")
        print(f"   dashboard accessible at {BASE_URL}/dashboard/{dashboard_id}")

        if d.data:
            print(f"   processing associated cards: {d.card_ids}")
            for card_id in d.card_ids:
                print(f"   card: {card_id} - {BASE_URL}/question/{card_id}")
                replace_table_in_cards([card_id], table)

            print("   Updating the dashboard...")
            d.update_parameters(table)
            print("   Update completed.")

            d.save()
            print("   Dashboard saved.")
        else:
            print(
                f"   Nothing to process dashboard {dashboard_id} is probably already archived."
            )

        print(f"** END - Processing Dashboard {dashboard_id} **")


def print_related_objects(table: Table) -> None:
    """
    Prints URLs for dashboards and cards associated with the given table.
    """

    print(f"Dashboards associated with {table.old}: {table.dashboard_ids}")
    for dashboard_id in table.dashboard_ids:
        print(f"{BASE_URL}/dashboard/{dashboard_id}")
    print(f"Cards associated with {table.old}: {table.card_ids}")
    for card_id in table.card_ids:
        print(f"{BASE_URL}/question/{card_id}")


# use it for development or debugging purpose
default_arguments = {
    "old": "old_schema.old_table",  # e.g. "old_schema.old_table",
    "new": "new_schema.new_table",  # e.g. "new_schema.new_table",
    "list": True,  # e.g. True/False
    "all": False,  # e.g. True/False
    "card_ids": None,  # e.g. "232 2323 23323"
    "dashboard_ids": None,  # e.g. "232 2323 23323"
    "renamed_columns": None,  # e.g '{"successfull_connections":"successful_connections"}',
}


def get_arguments(cli_args: list[str]):

    cli_args = sys.argv
    if len(cli_args) == 1:
        if default_arguments["old"]:
            cli_args.extend(["-o", default_arguments["old"]])
        if default_arguments["new"]:
            cli_args.extend(["-n", default_arguments["new"]])
        if default_arguments["list"]:
            cli_args.extend(["-l"])
        if default_arguments["all"]:
            cli_args.extend(["-a"])
        if default_arguments["card_ids"]:
            cli_args.extend(["-c", default_arguments["card_ids"]])
        if default_arguments["dashboard_ids"]:
            cli_args.extend(["-d", default_arguments["dashboard_ids"]])
        if default_arguments["renamed_columns"]:
            cli_args.extend(["-r", default_arguments["renamed_columns"]])

    parser = argparse.ArgumentParser(
        description="Update Metabase cards to use a new table."
    )
    parser.add_argument(
        "-o",
        "--old_table",
        required=True,
        help="Name of the old table (e.g., 'old_schema.old_table')",
    )
    parser.add_argument(
        "-n",
        "--new_table",
        required=True,
        help="Name of the new table (e.g., 'new_schema.new_table')",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all depended cards and dashboards",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Use this flag to update all depended cards and dashboards",
    )
    parser.add_argument(
        "-c",
        "--card_ids",
        nargs="+",
        type=int,
        help="List of card IDs to update",
    )
    parser.add_argument(
        "-d",
        "--dashboard_ids",
        nargs="+",
        type=int,
        help="List of dashboards IDs to update",
    )
    parser.add_argument(
        "-r",
        "--renamed_columns",
        type=json.loads,
        help="List of old_name:new_name pairs for columns renamed during the migration",
    )
    args = parser.parse_args()

    if not (args.list or args.card_ids or args.dashboard_ids or args.all):
        parser.error(
            "At least one of -l/--list, -a/--all, -c/--card_ids, or -d/--dashboard_ids must be specified."
        )

    return args


if __name__ == "__main__":
    # For development and debuging purpose. In case it's executed without arguments it gets the values from the default_arguments object
    args = get_arguments(sys.argv)

    table = Table(
        old=args.old_table,
        new=args.new_table,
        renamed_columns=args.renamed_columns,
        collect_all=args.all or args.list,
    )

    card_ids = args.card_ids
    dashboard_ids = args.dashboard_ids

    if card_ids:
        replace_table_in_cards(card_ids, table)
    if dashboard_ids:
        replace_table_in_dashboards(dashboard_ids, table)
    if args.all:
        print_related_objects(table)
        print(
            f"Processing dashboards associated to table {table.old}: {table.dashboard_ids}"
        )
        replace_table_in_dashboards(table.dashboard_ids, table)

        print(f"Processing cards associated to table {table.old}: {table.card_ids}")
        replace_table_in_cards(table.card_ids, table)
        print_related_objects(table)
    if args.list:
        print_related_objects(table)
