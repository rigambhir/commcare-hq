from couchdbkit.ext.django.schema import *
from corehq.apps.sms.models import SMSLog

PROFILE_A = "A"
PROFILE_B = "B"
PROFILE_C = "C"
PROFILE_D = "D"
PROFILE_E = "E"
PROFILE_F = "F"
PROFILE_G = "G"
PROFILE_H = "H"
PROFILES = [PROFILE_A, PROFILE_B, PROFILE_C, PROFILE_D, PROFILE_E, PROFILE_F, PROFILE_G, PROFILE_H]
PROFILE_DESC = {
    PROFILE_A : "A - HIV+",
    PROFILE_B : "B - ART non",
    PROFILE_C : "C - IDU",
    PROFILE_D : "D - PSE/CSV",
    PROFILE_E : "E - Top",
    PROFILE_F : "F - Bottom",
    PROFILE_G : "G - General",
    PROFILE_H : "H - Other",
}

class FRIMessageBankMessage(Document):
    """
    Defines a message in the message bank.
    """
    domain = StringProperty()
    risk_profile = StringProperty(choices=PROFILES)
    message = StringProperty()
    fri_id = StringProperty()

class FRIRandomizedMessage(Document):
    """
    Links a CommCareCase (study participant) to an FRIMessageBankMessage, assigning the order in
    which the message must be sent.
    """
    domain = StringProperty()
    case_id = StringProperty() # Points to the _id of the CommCareCase who this message was randomized for
    message_bank_message_id = StringProperty() # Points to the _id of a MessageBankMessage
    order = IntegerProperty() # The order in which this message must be sent, from 0 - 279

class FRISMSLog(SMSLog):
    fri_message_bank_lookup_completed = BooleanProperty(default=False)
    fri_message_bank_message_id = StringProperty()
    fri_id = StringProperty()
    fri_risk_profile = StringProperty(choices=PROFILES)

