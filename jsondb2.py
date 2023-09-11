#
#      Idea:
# Make nicely json serializable dict, that's all
#
from typing import Any, Type
import json


class db_schema:
    pass


class Database:
    def __init__(self, path: str, schema: Type[db_schema]) -> None:
        assert path.endswith(".json")
        assert issubclass(schema, db_schema)

        self._is_open = False
        self.path = path

        self.schema = schema
        self.schema_types = {}
        try:
            with open(self.path) as file:
                self.data = json.load(file)
        except FileNotFoundError:
            self.data = {}
        assert self.validate_schema()

    def validate_schema(self) -> bool:
        for key, value in self.schema.__dict__.items():
            if key.startswith("_"):
                continue
            v = self.data.get(key)
            if v == None:
                self.data[key] = {}
            self.schema_types[key] = value
        return True

    def __enter__(self):
        self._is_open = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._is_open = False
        self.save()

    def save(self):
        json = self.toJSON()
        with open(self.path, "w") as file:
            file.write(json)

    def toJSON(self):
        class Encoder(json.JSONEncoder):
            def default(self2, obj):  # type: ignore
                if type(obj) in self.schema_types.values():
                    return obj.pk  # type: ignore
                return json.JSONEncoder.default(self2, obj)

        return json.dumps(self.data, indent=2, cls=Encoder)

    def __getattr__(self, __name: str) -> "ObjectManager":
        for k, v in self.schema.__dict__.items():
            if type(v) == type:
                if __name == k:
                    if k.islower:
                        return ObjectManager(self, k, v)
        super().__getattribute__(__name)
        raise ValueError("THIS IS NOT REACHABLE")


class ObjectManager:
    def __init__(self, db: Database, name: str, cls) -> None:
        assert name.islower()
        self.name = name
        self.db = db
        self.cls = cls
        self.fields = {}
        self.fields_of = {}
        for field, tpe in cls.__annotations__.items():
            if type(tpe) == str:
                ev = eval(tpe.split("[")[0])
                self.fields[field] = ev
                if ev in (list, set, ):
                    self.fields_of[field] = eval(tpe.split("[")[1].strip("[]"))
            else:
                self.fields[field] = tpe

    def __repr__(self) -> str:
        return f"<Manager <{self.name}>>"

    def get(self, pk: int):
        keys = self.db.data[self.name].keys()
        if pk not in (int(key) for key in keys):
            raise KeyError(f"None with that id {pk}")

        obj: dict = self.db.data[self.name][str(pk)]

        inst = self.cls()
        setattr(inst, "pk", pk)
        for k, v in obj.items():
            if self.fields[k] in self.db.schema_types.values():
                for key, val in self.db.schema_types.items():
                    if val == self.fields[k]:
                        # same as : self.db.person.get(pk)
                        instance = getattr(self.db, key).get(v)
                        setattr(inst, k, instance)
                        break
                else:
                    raise KeyError("Did not break out like expected")
                continue
            elif type(v) in (list, set):
                if self.fields_of[k] in self.db.schema_types.values():
                    for key, val in self.db.schema_types.items():
                        if val == self.fields_of[k]:
                            # same as above but iterator
                            instances = [getattr(self.db, key).get(pk) for pk in v]
                            setattr(inst, k, instances)
                            break
                    else:
                        raise KeyError("Did not break out like expected")
                    continue
                else:
                    setattr(inst, k, v)
            else:
                setattr(inst, k, v)

        def _common_repr(self):
            fields = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
            fields_s = ",".join((f"({k}:{v})" for k, v in fields.items()))
            return f"<{self.__class__.__name__} {fields_s}>"

        inst.__class__.__repr__ = _common_repr

        return inst

    def create(self, **kwargs):
        if not (set(kwargs) == set(self.fields)):
            raise ValueError(f"Not perfect match {set(kwargs)} {set(self.fields)}")

        for k, v in kwargs.items():
            assert isinstance(
                v, self.fields[k]
            ), f"{v} not of {self.fields[k]} instead is {type(v)}"

        keys = self.db.data[self.name].keys()
        if len(keys) > 0:
            next_empty_pk = max((int(key) for key in keys)) + 1
        else:
            next_empty_pk = 0
        self.db.data[self.name][next_empty_pk] = {**kwargs}


# The definer zone


class oma_schema(db_schema):
    class person:
        name: str
        contacts: "list[oma_schema.person]"
        balance: float

    class bill:
        from_: "oma_schema.person"
        to: "oma_schema.person"
        amount: float
    
    class login:
        username: str
        password: str
        user: "oma_schema.person"


with Database("jsondb2.json", schema=oma_schema) as db:
    p: oma_schema.person = db.person.get(3)
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 117, in <listcomp>
    #     instances = [getattr(self.db, key).get(pk) for pk in v]
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 117, in get
    #     instances = [getattr(self.db, key).get(pk) for pk in v]
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 117, in <listcomp>
    #     instances = [getattr(self.db, key).get(pk) for pk in v]
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 117, in get
    #     instances = [getattr(self.db, key).get(pk) for pk in v]
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 117, in <listcomp>
    #     instances = [getattr(self.db, key).get(pk) for pk in v]
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 67, in __getattr__
    #     return ObjectManager(self, k, v)
    # File "/home/julius/Työpöytä/PyPy/jsondb2.py", line 82, in __init__
    #     ev = eval(tpe.split("[")[0])
    # RecursionError: maximum recursion depth exceeded during compilation
