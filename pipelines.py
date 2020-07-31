import json


class FreelancerScraperPipeline:
    def open_spider(self):
        print("Writing output file...")
        self.file = open('freelancer.json', 'w', encoding='utf-8')
        self.file.write("[\n")

    def close_spider(self):
        print("Closing output file...")
        self.file.write("]")
        self.file.close()

    '''
    Dumps the data from the model intto the json file
    '''
    def process_item(self, item):
        print("Writing freelancer data...")
        line = json.dumps(
            item,
            indent=4,
            # sort_keys=True,
            ensure_ascii=False,
            separators=(',', ': ')
        ) + ",\n"
        self.file.write(line)
        return item