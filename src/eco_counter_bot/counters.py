from string import Template

from eco_counter_bot.models import CounterConfig

counters = [
    CounterConfig(id="viaduc", name="Viaduc",           url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100065111?idOrganisme=4586&idPdc=100065111&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101065111%3B102065111")),
    CounterConfig(id="lift",   name="Pfaffenthal-Lift", url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136902?idOrganisme=4586&idPdc=100136902&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136902%3B102136902%3B103136902%3B104136902")),
    CounterConfig(id="glacis", name="Glacis",           url_template=Template("https://www.eco-visio.net/api/aladdin/1.0.0/pbl/publicwebpageplus/data/100136901?idOrganisme=4586&idPdc=100136901&fin=$end_date&debut=$start_date&interval=$interval&flowIds=101136901%3B102136901%3B103136901%3B104136901%3B105136901%3B106136901%3B107136901%3B108136901"))
]
