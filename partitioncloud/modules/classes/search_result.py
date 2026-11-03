class SearchResult():
    def __init__(self, name, uuid, url):
        self.name = name
        self.uuid = uuid
        self.source_url = url

    @property
    def thumbnail(self) -> str:
        return f"/thumbnails/search/{self.uuid}.jpg"

    @property
    def pdf_url(self) -> str:
        return f"/partition/search/{self.uuid}"

    def __repr__(self):
        return f"<SearchResult '{self.name}'>"