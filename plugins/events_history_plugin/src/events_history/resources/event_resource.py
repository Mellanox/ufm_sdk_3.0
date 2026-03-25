from resources.base_resource import BaseResource
from constants.events_constants import EventsConstants


class EventResource(BaseResource):
    BaseResource.ATTRS.update({
        EventsConstants.ID:EventsConstants.ID,
        EventsConstants.NAME: EventsConstants.NAME,
        EventsConstants.TYPE: EventsConstants.TYPE,
        EventsConstants.EVENT_TYPE: EventsConstants.EVENT_TYPE,
        EventsConstants.SEVERITY: EventsConstants.SEVERITY,
        EventsConstants.TIMESTAMP: EventsConstants.TIMESTAMP,
        EventsConstants.COUNTER: EventsConstants.COUNTER,
        EventsConstants.CATEGORY: EventsConstants.CATEGORY,
        EventsConstants.OBJECT_NAME: EventsConstants.OBJECT_NAME,
        EventsConstants.OBJECT_PATH: EventsConstants.OBJECT_PATH,
        EventsConstants.WRITE_TO_SYSLOG: EventsConstants.WRITE_TO_SYSLOG,
        EventsConstants.DESCRIPTION: EventsConstants.DESCRIPTION
        })

    def __init__(self, obj):
        super(EventResource, self).__init__(obj)
        # TODO convert timestamp to UTC
