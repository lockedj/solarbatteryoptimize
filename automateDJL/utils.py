import os
import platform
import configparser
import logging
import keyring
try:
    from keyrings.cryptfile.cryptfile import CryptFileKeyring
except:
    pass


class Utils:

    def __init__(self, cfile="battery.conf"):
        self.configfile = cfile
        return

    def getKey(self, service, user):
        self.getKr()
        return keyring.get_password(service, user)

    def setKey(self, service, user, pwd):
        self.getKr()
        return keyring.set_password(service, user, pwd)

    def getKr(self):
        if os.name != 'nt':
            #logging.getLogger().exception("getlogger "+self.configfile)
            config = configparser.ConfigParser()
            config.read(self.configfile)
            sd = config.get("other", "startdate")
            pc = config.get("other", "postcode")

            kr = CryptFileKeyring()
            kr.keyring_key = pc+platform.node()+os.name+sd+"!djl!"
            keyring.set_keyring(kr)
