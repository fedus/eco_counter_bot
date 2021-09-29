from enum import Enum
from string import Template

class Interval(Enum):
    DAYS = 4
    WEEKS = 5
    MONTHS = 6

class CounterConfig:

    def __init__(self, name: str, url_template: Template):
        self.name = name
        self.url_template = url_template

class CounterService:

    def __init__(self, counters: list[CounterConfig]):
        self.counters = counters

counters = [ 
    CounterConfig("viaduc", Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100065111?idOrganisme=4586&idPdc=100065111&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101065111%3B102065111")),
    CounterConfig("lift", Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136902?idOrganisme=4586&idPdc=100136902&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136902%3B102136902%3B103136902%3B104136902")),
    CounterConfig("glacis", Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136901?idOrganisme=4586&idPdc=100136901&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136901%3B102136901%3B103136901%3B104136901%3B105136901%3B106136901%3B107136901%3B108136901"))
]

service = CounterService(counters)
