from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig


class UserInteractionConfig(BaseEventHandleProviderConfig):
    pass


class UserInteractionProvider(BaseEventHandleProvider):
    def handle_event(self, event, context):
        return
