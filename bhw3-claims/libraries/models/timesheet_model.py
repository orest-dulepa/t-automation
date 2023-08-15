import datetime
from libraries.models.client_model import ClientModel
from libraries.models.provider_model import ProviderModel


class TimesheetModel:
    id: str = ''
    time_str: str = ''
    time_from: datetime = None
    time_to: datetime = None
    date: datetime = None
    date_str: str = ''
    client: ClientModel = None
    provider_id: str =''
    location: str =''
    amount_owed: str =''
    client_id: str =''
    service_auth: str = ''
    procedure_code_id: str =''
    units_of_service: str = ''
    time_worked_in_mins: str = ''