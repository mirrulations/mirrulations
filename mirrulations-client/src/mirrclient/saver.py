class Saver:
    """
    A class which encapsulates the saving for the Client
    A Saver has a list of savers which are other classes
    ...
    Methods
    -------
    save_json(path = string, data = response)

    save_binary(path = string, data, = response.content)
    """
    def __init__(self, savers=None) -> None:
        """
        Parameters
        ----------
        savers : list
            A list of Saver Objects Ex: S3Saver(), DiskSaver()
        """
        self.savers = savers

    def save_json(self, path, data):
        """
        Iterates over the instance variable savers list
        and calls the corresponding subclass save_json() method.

        Parameters
        ----------
        path : str
            A string denoting where the json file should be saved to.

        data: dict
            The json as a dict to save.
        """
        for saver in self.savers:
            saver.save_json(path, data)

    def save_binary(self, path, binary):
        """
        Iterates over the instance variable savers list
        and calls the corresponding subclass save_binary() method.

        Parameters
        ----------
        path : str
            A string denoting where the binary file should be saved to.

        binary: bytes
            The binary response.content returns.
        """
        for saver in self.savers:
            saver.save_binary(path, binary)

    def save_text(self, path, text):
        """
        Iterates over the instance variable savers list
        and calls the corresponding subclass save_text() method.

        Parameters
        ----------
        path : str
            A string denoting where the binary file should be saved to.

        text : str
            The extracted text to be saved
        """
        for saver in self.savers:
            saver.save_text(path, text)
