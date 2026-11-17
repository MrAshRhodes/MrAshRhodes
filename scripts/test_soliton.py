import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from io import BytesIO

import soliton


class RadarTests(unittest.TestCase):
    def test_streak_edges(self):
        for counts, expected in [
            ([], (0, 0)),
            ([0], (0, 0)),
            ([1, 2, 0], (2, 2)),
            ([1, 0, 0], (0, 1)),
            ([1, 2, 0, 3], (1, 2)),
            ([1, 1, 1], (3, 3)),
        ]:
            with self.subTest(counts=counts):
                self.assertEqual(
                    soliton.streaks([{"contributionCount": n} for n in counts]),
                    expected,
                )

    def test_short_calendar(self):
        calendar = {
            "totalContributions": 3,
            "weeks": [{"contributionDays": [
                {"date": "2026-11-15", "weekday": 0, "contributionCount": 1, "contributionLevel": "FIRST_QUARTILE"},
                {"date": "2026-11-16", "weekday": 1, "contributionCount": 2, "contributionLevel": "FOURTH_QUARTILE"},
                {"date": "2026-11-17", "weekday": 2, "contributionCount": 0, "contributionLevel": "NONE"},
            ]}],
        }
        root = ET.fromstring(soliton.render(calendar))
        ns = {"s": "http://www.w3.org/2000/svg"}
        title = root.find("s:title", ns).text
        self.assertIn("current streak 2 days", title)
        self.assertIn("active on 2 of the last 3 days", title)
        text = " ".join("".join(n.itertext()) for n in root.findall("s:text", ns))
        self.assertIn("PEAK DAY // 16 NOV", text)
        self.assertIn("2/3", text)
        self.assertEqual(len(root.findall("s:rect[@class='p']", ns)), 2)

    def test_graphql_errors_are_not_rendered_as_success(self):
        with patch.dict("os.environ", {"GITHUB_USER": "example", "GITHUB_TOKEN": "test"}):
            with patch("urllib.request.urlopen", return_value=BytesIO(b'{"errors":[{"message":"denied"}]}')):
                with self.assertRaisesRegex(SystemExit, "GraphQL error"):
                    soliton.fetch_calendar()


if __name__ == "__main__":
    unittest.main()
