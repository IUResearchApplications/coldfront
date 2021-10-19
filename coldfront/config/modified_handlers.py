from logging import handlers


class TimedRotatingFileHandler(handlers.TimedRotatingFileHandler):
    def rotation_filename(self, default_name):
        """
        Modify the file name so the date is before the file extension.
        """
        base_filename, ext, date = default_name.split(".")
        return "{}.{}.{}".format(base_filename, date, ext)
