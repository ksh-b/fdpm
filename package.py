class Package:
    installer = ""

    def __init__(self, name=None, description=None, id_=None, url: str = None, installer=None):
        self.version = -1
        self.name = name
        self.description = description
        self.url = url
        if url is not None:
            self.id_ = url.split('/')[-1]
        else:
            self.id_ = id_
        self.installer = installer

    def __str__(self):
        return str({
            "name": self.name,
            "description": self.description,
            "id": self.id_,
            "url": self.url,
            "installer": self.installer
        })
