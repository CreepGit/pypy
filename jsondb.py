import json
from typing import Any

class DB:
    _data: "dict[str, dict]"
    
    def __init__(self, *, schema: "dict[str, dict]"={}) -> None:
        self.load()
        self.schema = schema

    def load(self):
        with open("jsondb.json", "r") as file:
            self._data = json.load(file)
        print("Loaded db state")
    
    def validateWithSchema(self, validateThisInstead = None):
        data: dict = validateThisInstead or self._data
        if not self.schema:
            print("No schema to compare against!")
            return
        for key, ids in data.items():
            if key not in self.schema.keys():
                raise AssertionError(f"Schema validation failed '{key}' not in 'schema keys'")
            for _id, instance in ids.items():
                for key2, instanceValue in instance.items():
                    if key2 not in self.schema[key].keys():
                        raise AssertionError(f"Schema validation failed '{key2}' not in 'schema {key} keys'")

    def save(self):
        with open("jsondb.json", "w") as file:
            json.dump(self._data, file, indent=2)
        print("Saved db state")
        
    def __getattr__(self, name: str):
        return self[name]

    def __getitem__(self, name: str) -> "ObjectManager":
        if name not in self._data.keys():
            raise AttributeError(f"DB has no schema for {name}")
        return ObjectManager(self._data[name], self.schema[name])

class ObjectManager:
    def __init__(self, data, innerSchema) -> None:
        self.data: dict = data
        self.schema: "dict[str, Any]" = innerSchema
    
    def get(self, value):
        default_values = {k:None if isinstance(v, str) else v() for k,v in self.schema.items()}
        values = {k:db[self.schema[k]].get(v) if isinstance(self.schema[k], str) else v for k,v in self.data[str(value)].items()}
        return {**default_values, **values, "pk": str(value)}

    def add(self, key, value):
        self.data[str(key)] = value
    
    def __str__(self) -> str:
        widths = [len(field) for field in self.schema.keys()]
        for _id, instance in self.data.items():
            for column_i, (key, value) in enumerate(instance.items()):
                lenVal = len(value)
                if lenVal > widths[column_i]:
                    widths[column_i] = lenVal
        
        lines = ""
        for column_i, key in enumerate(self.schema.keys()):
            lines += f"{key:{widths[column_i]}}  "
        lines += "\n"
        for _id, instance in self.data.items():
            for column_i, (key, value) in enumerate(instance.items()):
                lines += f"{value:{widths[column_i]}}  "
            lines += "\n"
        return f"{lines}"
    
class IdLink:
    pass

db = DB(schema={
    "user": {
        "name": str,
        "description": str,
        "friend": "user",
    },
})

user = db.user.get(2)
user["friend"] = "1"
print(user)

db.validateWithSchema()


db.save()