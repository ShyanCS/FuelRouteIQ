import re
import unicodedata

US_STATES = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
)
CANADIAN_STATES = frozenset("AB BC MB NB NL NS NT NU ON PE QC SK YT".split())
STATE_NAMES = dict(
    zip(
        "alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming|district of columbia".split(
            "|"
        ),
        "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split(),
        strict=True,
    )
)


def clean(value):
    return " ".join(str(value or "").split())


def city_key(value):
    value = (
        unicodedata.normalize("NFKD", clean(value)).encode("ascii", "ignore").decode().casefold()
    )
    value = re.sub(r"\s+\(balance\)$", "", value)
    value = re.sub(r"\s+(city|town|village|borough|municipality|cdp)$", "", value)
    value = re.sub(r"\bst[.]?\s+", "saint ", value)
    return value
