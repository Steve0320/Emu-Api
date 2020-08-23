from xml.etree import ElementTree


# Base class for a response entity. All individual response
# objects inherit from this.
class Entity:

    def __init__(self, tree):

        self._tree = tree
        self.fresh = True

        # These tags are common to all responses
        self.device_mac = self.find_text('DeviceMacId')

        self._parse()

    def __repr__(self):
        return ElementTree.tostring(self._tree).decode('ASCII')

    # Hook for subclasses to override to provide special parsing
    # for computing their parameters.
    def _parse(self):
        return

    def find_text(self, tag):
        node = self._tree.find(tag)
        if node is None:
            return None
        return node.text

    # The root element associated with this class
    @classmethod
    def tag_name(cls):
        return cls.__name__

    # Map the tag name to the type of subclass
    @classmethod
    def tag_to_class(cls, tag):
        for klass in cls.__subclasses__():
            if klass.tag_name() == tag:
                return klass
        return None


#####################################
#       Raven Notifications         #
#####################################

class ConnectionStatus(Entity):
    def _parse(self):
        self.meter_mac = self.find_text('MeterMacId')
        self.status = self.find_text("Status")
        self.description = self.find_text("Description")
        self.status_code = self.find_text("StatusCode")         # 0x00 to 0xFF
        self.extended_pan_id = self.find_text("ExtPanId")
        self.channel = self.find_text("Channel")                # 11 to 26
        self.short_address = self.find_text("ShortAddr")        # 0x0000 to 0xFFFF
        self.link_strength = self.find_text("LinkStrength")     # 0x00 to 0x64


class DeviceInfo(Entity):
    def _parse(self):
        self.install_code = self.find_text("InstallCode")
        self.link_key = self.find_text("LinkKey")
        self.fw_version = self.find_text("FWVersion")
        self.hw_version = self.find_text("HWVersion")
        self.fw_image_type = self.find_text("ImageType")
        self.manufacturer = self.find_text("Manufacturer")
        self.model_id = self.find_text("ModelId")
        self.date_code = self.find_text("DateCode")


class ScheduleInfo(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.event = self.find_text("Event")
        self.frequency = self.find_text("Frequency")
        self.enabled = self.find_text("Enabled")


# TODO: There can be more than one MeterMacId
class MeterList(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")


#####################################
#       Meter Notifications         #
#####################################

class MeterInfo(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.meter_type = self.find_text("MeterType")
        self.nickname = self.find_text("NickName")
        self.account = self.find_text("Account")
        self.auth = self.find_text("Auth")
        self.host = self.find_text("Host")
        self.enabled = self.find_text("Enabled")


class NetworkInfo(Entity):
    def _parse(self):
        self.coordinator_mac = self.find_text("CoordMacId")
        self.status = self.find_text("Status")
        self.description = self.find_text("Description")
        self.status_code = self.find_text("StatusCode")
        self.extended_pan_id = self.find_text("ExtPanId")
        self.channel = self.find_text("Channel")
        self.short_address = self.find_text("ShortAddr")
        self.link_strength = self.find_text("LinkStrength")


#####################################
#        Time Notifications         #
#####################################

# TODO: Convert from Rainforest epoch
class TimeCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.utc_time = self.find_text("UTCTime")
        self.local_time = self.find_text("LocalTime")


#####################################
#      Message Notifications        #
#####################################

class MessageCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_text("TimeStamp")
        self.id = self.find_text("Id")
        self.text = self.find_text("Text")
        self.confirmation_required = self.find_text("ConfirmationRequired")
        self.confirmed = self.find_text("Confirmed")
        self.queue = self.find_text("Queue")


#####################################
#        Price Notifications        #
#####################################

class PriceCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_text("TimeStamp")
        self.price = self.find_text("Price")
        self.currency = self.find_text("Currency")      # ISO-4217
        self.trailing_digits = self.find_text("TrailingDigits")
        self.tier = self.find_text("Tier")
        self.tier_label = self.find_text("TierLabel")
        self.rate_label = self.find_text("RateLabel")


#####################################
#   Simple Metering Notifications   #
#####################################

class InstantaneousDemand(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_text("TimeStamp")
        self.demand = int(self.find_text("Demand") or "0x00", 16)
        self.multiplier = int(self.find_text("Multiplier") or "0x00", 16)
        self.divisor = int(self.find_text("Divisor") or "0x00", 16)
        self.digits_right = self.find_text("DigitsRight")
        self.digits_left = self.find_text("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")

        # Compute actual reading (protecting from divide-by-zero)
        if self.divisor != 0:
            self.reading = self.demand * self.multiplier / float(self.divisor)
        else:
            self.reading = 0


class CurrentSummationDelivered(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_text("TimeStamp")
        self.summation_delivered = self.find_text("SummationDelivered")
        self.summation_received = self.find_text("SummationReceived")
        self.multiplier = self.find_text("Multiplier")
        self.divisor = self.find_text("Divisor")
        self.digits_right = self.find_text("DigitsRight")
        self.digits_left = self.find_text("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")


class CurrentPeriodUsage(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_text("TimeStamp")
        self.current_usage = self.find_text("CurrentUsage")
        self.multiplier = self.find_text("Multiplier")
        self.divisor = self.find_text("Divisor")
        self.digits_right = self.find_text("DigitsRight")
        self.digits_left = self.find_text("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")
        self.start_date = self.find_text("StartDate")


class LastPeriodUsage(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.last_usage = self.find_text("LastUsage")
        self.multiplier = self.find_text("Multiplier")
        self.divisor = self.find_text("Divisor")
        self.digits_right = self.find_text("DigitsRight")
        self.digits_left = self.find_text("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")
        self.start_date = self.find_text("StartDate")
        self.end_date = self.find_text("EndDate")


# TODO: IntervalData may appear more than once
class ProfileData(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.end_time = self.find_text("EndTime")
        self.status = self.find_text("Status")
        self.period_interval = self.find_text("ProfileIntervalPeriod")
        self.number_of_periods = self.find_text("NumberOfPeriodsDelivered")
        self.interval_data = self.find_text("IntervalData")
