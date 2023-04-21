from json import load
import os


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

    def save_meta(self, path, meta):
        """
        Iterates over the instance variable savers list
        and calls the corresponding subclass save_binary() method.

        Parameters
        ----------
        path : str
            A string denoting where the metadata file should be saved to.

         meta: dict
            The metadata (json) to be saved
        """
        for saver in self.savers:
            saver.save_meta(path, meta)

    @staticmethod
    def update_meta(path, meta):
        """
        If an existing metadata file exists,
        the new meta is updated with the previous
        meta's extraction status.
        Parameters
        ----------
        path : str
            The path to the metadata file
        meta : dict
            The new metadata to be written/combined
        """
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                previous_meta = load(file)
            for key in previous_meta["extraction_status"]:
                meta['extraction_status'][key] = "Not Attempted"
            print("extraction-metadata.json file exists. Updating this file")
