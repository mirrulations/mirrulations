class Saver:
    """
    A class which takes the content of an attachment (pdf, doc, etc.), and saves it to a given path.
    ...
    Methods
    -------
    save(content = response, path = string)
        Takes the content (pdf, doc, etc.) and saves the attachment to a given path
    """
    def save(self, content, path):
        with open(f'/data{path}', "wb") as file:
            file.write(content)
            file.close()
