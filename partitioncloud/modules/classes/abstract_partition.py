class AbstractPartition():
    def __init__(self):
        self.name = None
        self.uuid = None

    @property
    def thumbnail(self) -> str:
        raise NotImplementedError

    @property
    def pdf_url(self) -> str:
        raise NotImplementedError

    def __repr__(self):
        return f"<AbstractPartition '{self.name}'>"