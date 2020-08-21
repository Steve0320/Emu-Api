from xml.etree import ElementTree


# Base class for a response entity. All individual response
# objects inherit from this.
class Entity:

    def __init__(self, tree):
        self._tree = tree
        self.fresh = True
        self._parse()

    def __repr__(self):
        return ElementTree.dump(self._tree)

    # Hook for subclasses to override to provide special parsing
    # for computing their parameters.
    def _parse(self):
        return

    def find_text(self, tag):
        return self._tree.find(tag).text

    # Map the tag name to the type of subclass
    @staticmethod
    def tag_to_class(text):
        mappings = {
            'InstantaneousDemand': InstantaneousDemand
        }
        return mappings.get(text)


class InstantaneousDemand(Entity):
    def _parse(self):
        self.demand = self.find_text("Demand")
        self.multiplier = self.find_text("Multiplier")
        self.divisor = self.find_text("Divisor")


class CurrentSummationDelivered(Entity):
    def _parse(self):
        return


class CurrentPrice(Entity):
    def _parse(self):
        return


class DeviceInfo(Entity):
    def _parse(self):
        return


class ConnectionStatus(Entity):
    def _parse(self):
        return


class MessageCluster(Entity):
    def _parse(self):
        return


class TimeCluster(Entity):
    def _parse(self):
        return


class NetworkInfo(Entity):
    def _parse(self):
        return


class PriceCluster(Entity):
    def _parse(self):
        return


class ScheduleInfo(Entity):
    def _parse(self):
        return


class BlockPriceDetail(Entity):
    def _parse(self):
        return
