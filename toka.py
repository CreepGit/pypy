import json

database = {}

class BanaaniMeta(type):
    def __repr__(self):
        return "META"
    
    def __call__(self):
        pass

class Banaani(metaclass=BanaaniMeta):
    def __repr__(self):
        return "OLEN BANAANI"


banaani_instanssi = Banaani()

help(banaani_instanssi)

