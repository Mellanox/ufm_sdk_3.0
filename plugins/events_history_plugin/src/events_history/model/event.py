class Event:

    def __init__(self, id, name, event_type, severity, timestamp, category, description, object_name,
                 object_path, write_to_syslog=False, type="N/A", counter="N/A"):
        self.id = id
        self.name = name
        self.type = type
        self.event_type = event_type
        self.severity = severity
        self.timestamp = timestamp
        self.counter = counter
        self.category = category
        self.object_name = object_name
        self.object_path = object_path
        self.write_to_syslog = write_to_syslog
        self.description = description

