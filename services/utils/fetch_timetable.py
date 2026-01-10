import asyncio

import aiohttp
from bs4 import BeautifulSoup


class TimetableFetcher:
    def __init__(self, request_url: str = "https://zpa.cs.hm.edu/public/course_plan/", group: str = "248", module: str = ""):
        self.request_url = request_url
        self.group = group
        self.module = module

    @staticmethod
    def timetable_to_dict(html: str):
        soup = BeautifulSoup(html, "lxml")

        timetable = []
        plan = soup.find("tbody", {"class": "plan"})
        if not plan:
            return timetable

        for row in plan.find_all("tr"):
            time_cell = row.find("td", class_="time")
            if not time_cell:
                continue
            slot = {"time": time_cell.get_text(strip=True), "courses": []}
            for td in row.find_all("td"):
                if td is time_cell:
                    continue
                for block in td.select("div.timeslot_blue, div.timeslot_red"):
                    title = block.select_one("strong a")
                    details = [t.strip() for t in block.stripped_strings]
                    slot["courses"].append(
                        {
                            "title": title.get_text(strip=True) if title else None,
                            "details": details[2:],
                        }
                    )
            timetable.append(slot)
        return timetable

    @staticmethod
    def extract_class_ids(html: str):
        soup = BeautifulSoup(html, "lxml")
        select = soup.find("select", id="id_group")
        if not select:
            return []
        return [
            {"value": option.get("value", ""), "label": option.get_text(strip=True)}
            for option in select.find_all("option")
        ]

    async def fetch_and_parse_timetable(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.request_url) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                token_element = soup.select_one("input[name=csrfmiddlewaretoken]")
                if token_element is None:
                    raise ValueError("CSRF token not found in the response")
                token = token_element["value"]

            data = {"csrfmiddlewaretoken": token, "group": self.group, "module": self.module}
            headers = {"Referer": self.request_url}

            async with session.post(self.request_url, data=data, headers=headers) as resp:
                timetable = self.timetable_to_dict(await resp.text())
                return timetable


async def main():
    fetcher = TimetableFetcher()
    timetable = await fetcher.fetch_and_parse_timetable()
    print(timetable)


if __name__ == "__main__":
    asyncio.run(main())