import time

from libraries import config
from libraries import common as com
from libraries.central_reach.central_reach_process.centarl_reach_conduct_audit import CentralReachConductAudit
from libraries.models.edit_timesheet_kaiser_model import EditTimesheetKaiserModel
from libraries.models.payor_model import PayorModel


class ProcessConductAudit:

    def __init__(self,central_reach_object):
        self.cr: CentralReachConductAudit = central_reach_object

    def add_modifier_value(self, payor_modifier, is_only_telehealth = True):
        if payor_modifier:
            com.log_message(f"Provisions - Add '{payor_modifier}' Modifier for Telehealth Sessions ")
            timesheets_url = self.cr.browser.location

            if is_only_telehealth:
                self.cr.set_telehealth_location()

            timesheet_ids = self.cr.get_timesheet_ids()
            for index, item_id in enumerate(timesheet_ids):
                is_success = False
                count = 0
                attempts = 3
                exception: Exception = Exception()
                while (count < attempts) and (is_success is False):
                    try:
                        self.cr.add_modifier_using_edittimesheet(timesheetId=item_id, modifier=payor_modifier)
                        is_success = True
                    except Exception as ex:
                        time.sleep(3)
                        exception = Exception(f"Error of timesheet {item_id} - " + str(ex))
                        count += 1

                if is_success is False:
                    raise exception


                if index % 100 == 0 and index > 0:
                    com.log_message(f'{index} timesheets checked on modifier "{payor_modifier}"', 'INFO')

                if index == len(timesheet_ids) - 1:
                    com.log_message(f'{index} timesheets checked on modifier "{payor_modifier}"', 'INFO')

            self.cr.cr_main.go_to_by_link(timesheets_url)
            if is_only_telehealth:
                self.cr.close_locations_window()


    def location_audit(self) -> bool:
        com.log_message("Location Audit")
        excess_locations = self.cr.get_and_check_locations(config.ACCEPTABLE_LOCATIONS)
        if len(excess_locations) > 0:
            com.log_message(
                f"{str.join(', ', excess_locations)} - location(s) are not one of listed {config.ACCEPTABLE_LOCATIONS}","WARN")
            return False

        self.cr.close_locations_window()
        return True

    def duplicate_entries_audit(self) -> bool:
        com.log_message("Duplicate Entries Audit")
        duplicate_timesheet_ids = self.cr.get_duplicates_by_filter()
        if len(duplicate_timesheet_ids) > 0:
            com.log_message("Duplicates exist", "WARN")
            return False

        return True

    def overlapping_entries_audit_by_client(self, payor_id) -> str:
        com.log_message("Overlapping Entries Audit")
        reason_message: str = ''
        timesheets_data = self.cr.get_billing_timesheets_by_payor_id_and_overlapbyclient(payor_id)

        if len(timesheets_data) > 0:
            clients_ids = list(dict.fromkeys(map(lambda x: x.client.id, timesheets_data)))
            invalid_ids = list()
            for client_id in clients_ids:
                timesheets_by_client = list(filter(lambda x: x.client.id == client_id, timesheets_data))
                timesheet_ids = list(map(lambda x: x.id, timesheets_data))
                if any("97153" in x.service_auth for x in timesheets_by_client) and any("97155" in x.service_auth for x in timesheets_by_client):
                    invalid_ids.append(str(client_id))
                else:
                    invalid_ids.append(str(client_id))

                if len(invalid_ids) > 0:
                    reason_message = str.join(", ", invalid_ids)

        return reason_message

    def kaiser_process_overlapping(self, timesheets_kaiser) -> bool:
        com.log_message("Overlapping Entries Audit -  Kaiser Oregon (OR)")
        edit_timesheets_data = self.__get_overlapping_entries_audit_kaiser__()
        edit_timesheets_data_97155 = self.__get_entries_audit_kaiser_97155___(timesheets_kaiser,
                                                                              edit_timesheets_data)
        if len(edit_timesheets_data_97155) > 0:
            edit_timesheets_data +=edit_timesheets_data_97155
        self.__process_edit_timesheets_kaiser__(edit_timesheets_data)

        return True

    def __get_overlapping_entries_audit_kaiser__(self)-> list:
        edit_timesheets_data = list()
        timesheets_data = self.cr.get_billing_timesheets_by_payor_kaiser_and_overlapbyclient()

        if len(timesheets_data) >0:
            clients_ids = list(dict.fromkeys(map(lambda x: x.client.id, timesheets_data)))
            for client_id in clients_ids:
                timesheets_by_client = list(filter(lambda x: x.client.id == client_id, timesheets_data))
                if any("97153" in x.service_auth for x in timesheets_by_client) and any("97155" in x.service_auth for x in timesheets_by_client):
                    for item in timesheets_by_client:
                        edit_timesheet_obj = EditTimesheetKaiserModel()
                        edit_timesheet_obj.timesheet_id = item.id
                        edit_timesheet_obj.code = item.service_auth
                        edit_timesheet_obj.date_service = item.date
                        edit_timesheets_data.append(edit_timesheet_obj)
        return edit_timesheets_data

    def __get_entries_audit_kaiser_97155___(self,timesheets_data, edit_timesheets_data):
        new_edit_timesheets_data = list()
        if len(timesheets_data)>0:
            clients_ids = list(dict.fromkeys(map(lambda x: x.client.id, timesheets_data)))
            for client_id in clients_ids:
                timesheets_by_client = list(filter(lambda x: x.client.id == client_id, timesheets_data))
                ids_timesheets = list(map(lambda x: x.timesheet_id, edit_timesheets_data))
                for item in timesheets_by_client:
                    if "97155" in item.service_auth and not(item.id in ids_timesheets):
                        edit_timesheet_obj = EditTimesheetKaiserModel()
                        edit_timesheet_obj.timesheet_id = item.id
                        edit_timesheet_obj.code = item.service_auth
                        edit_timesheet_obj.date_service = item.date
                        edit_timesheet_obj.is_update_rates = False
                        new_edit_timesheets_data.append(edit_timesheet_obj)
        return new_edit_timesheets_data

    def __process_edit_timesheets_kaiser__(self, edit_timesheets_data):
        for edit_timesheet_item in edit_timesheets_data:
            self.cr.edit_timesheets_kaiser(edit_timesheet_item)

    def signature_audit(self):
        com.log_message("Signature Audit")
        self.cr.signed_by_client_no()
        self.cr.signed_by_client_yes()

    def telehealth_process_for_opum(self, timesheets_data):
        locations = self.get_locations_from_timesheets(timesheets_data)
        if any("Telehealth" in x for x in locations):
            self.cr.set_telehealth_location()
            self.cr.add_labels_covid_19_quartine()
            self.cr.remove_telehealth()
            self.cr.close_locations_window()

    def overlapping_entries_audit_by_provider(self, payor_id):
        com.log_message("Overlapping Entries Audit")
        timesheets_data = self.cr.get_billing_timesheets_by_payor_id_and_overlapbyclient(payor_id)
        if len(timesheets_data) > 0:
            com.log_message(f"Exist the timesheets overlapping by provider")

    def adjustments_for_promise_health_plan(self, payor_id) -> list:
        com.log_message("H0031, H0032, and H0046 Adjustments")
        link_inital = self.cr.get_link_url()
        self.cr.set_filter_covid_19()
        timesheets = self.cr.get_timesheet_for_promise_health_plan(payor_id)
        adjustments_timesheets = list()
        if len(timesheets) > 0:
            adjustments_codes = ["H0031", "H0032", "H0046"]
            for adjustments_code_item in adjustments_codes:
                selected_timesheets = self.cr.process_adjustments_by_service_code(adjustments_code_item, timesheets)
                if len(selected_timesheets) > 0:
                    adjustments_timesheets += selected_timesheets

        self.cr.go_to_back_by_link(link_inital)
        return adjustments_timesheets

    def get_locations_from_timesheets(self, timesheets) -> list:
        return self.cr.extract_locations_from_timesheets(timesheets)


