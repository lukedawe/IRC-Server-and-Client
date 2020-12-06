import re


class Client:
    __linesep_regexp = re.compile(rb"\r?\n")
    # The RFC limit for nicknames is 9 characters, but what the heck.
    __valid_nickname_regexp = re.compile(
        rb"^[][\`_^{|}A-Za-z][][\`_^{|}A-Za-z0-9-]{0,50}$"
    )
    __valid_channelname_regexp = re.compile(
        rb"^[&#+!][^\x00\x07\x0a\x0d ,:]{0,50}$"
    )
