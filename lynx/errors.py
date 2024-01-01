class NoAPIKeyInSettings(Exception):
  def __init__(self):
    super()

class UrlParseError(Exception):
  def __init__(self, http_err):
    super()
    self.http_error = http_err

class TagError(Exception):
  def __init__(self):
    super()