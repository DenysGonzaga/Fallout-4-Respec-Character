import os
import logging
import requests
from config import settings
from bs4 import BeautifulSoup
from typing import List
from collections import namedtuple

Perk = namedtuple(
    "Perk",
    ["name", "attribute_requirement", "rank", "level_requirement", "description", "id"],
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Fallout4Respec")


def retrieving_perks_data() -> List[Perk]:
    logger.info("Crawling Fallout 4 Perks Page.")
    html_data = requests.get(settings.internal.fallout_wiki_perks_url).content
    parsed_page = BeautifulSoup(html_data, "html.parser")

    tables = parsed_page.find_all(
        "table", class_="va-table va-table-full va-table-shaded sortable"
    )
    perks: List[Perk] = list()

    for table in tables:
        raw_data = []

        th = table.find_all("th")
        if len(th) > 2 and th[0].next == "Name\n" and th[1].next == "Attribute Rank\n":
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                cols = [ele.text.strip() for ele in cols]
                if cols != []:
                    raw_data.append([ele for ele in cols if ele])

            current_header = ""
            current_attribute_requirement = ""
            for rd in raw_data:
                if len(rd) == 0:
                    continue
                else:
                    if len(rd[-1]) == 8:
                        perk_id = [rd[-1]]
                    else:
                        perk_id = [rd[-1][0:8], rd[-1][8:16]]

                    if not rd[0].isdigit():
                        current_header = rd[0]
                        current_attribute_requirement = rd[1]
                        perks.append(
                            Perk(
                                name=current_header,
                                attribute_requirement=current_attribute_requirement,
                                rank=rd[2],
                                level_requirement=1,
                                description=rd[-2],
                                id=perk_id,
                            )
                        )
                    else:
                        perks.append(
                            Perk(
                                name=current_header,
                                attribute_requirement=current_attribute_requirement,
                                rank=rd[0],
                                level_requirement=rd[1],
                                description=rd[-2],
                                id=perk_id,
                            )
                        )

    return perks


def retrieving_char_data() -> dict:
    points_to_add = (
        settings.character.current_level - 1
    ) + settings.internal.initial_perk_points

    special_points = {"FreePoints": points_to_add}
    for special in settings.internal.special_names:
        if special in settings.character.boobleheads:
            special_points[special] = 2
        else:
            special_points[special] = 1

    return special_points


def generate_script(perks: List[Perk], char_points: dict) -> None:
    perks.sort(key=lambda x: x.rank, reverse=True)
    commands = []

    for pk in perks:
        for pkid in pk.id:
            commands.append(f"{settings.internal.remove_perk_cmd} {pkid};\n")

    for special, value in char_points.items():
        if special == "FreePoints":
            commands.append(f"{settings.internal.add_perk_points_cmd} {value};\n")
        else:
            commands.append(
                f"{settings.internal.set_special_value_cmd} {special.lower()} {value};\n"
            )

    filepath = os.path.join(
        settings.internal.game_data_path, settings.internal.script_name
    )

    try:
        with open(filepath, "w") as f:
            f.writelines(commands)

        logger.info(
            f"Script '{settings.internal.script_name}' generated on '{settings.internal.game_data_path}'"
        )
        logger.info(
            f"Just open console command and tip 'bat {settings.internal.script_name.split('.')[0]}'."
        )
    except Exception as e:
        logger.error(f"Failed to save script: {str(e)}")


def main():
    perks = retrieving_perks_data()
    char_points = retrieving_char_data()
    generate_script(perks, char_points)


if __name__ == "__main__":
    main()
