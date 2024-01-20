import re
from typing import Union, Dict
import json
# Third party
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# Application
import check_eu_service_status


class LookupVat:
    """
    Class to handle VAT lookup requests for EU member states. The lookup API has been changed from SOAP
    to REST which is more up-to-date and simpler to process.
    The following URL has (basic) technical information.
    https://ec.europa.eu/taxation_customs/vies/#/technical-information
    """
    def __init__(self) -> None:
        self.host = 'ec.europa.eu'
        self.service = '/taxation_customs/vies/rest-api/check-vat-number'
        # The *whole* dictionary (converted to JSON format) has to be passed to the REST connection,
        # but only 'countryCode' and 'vatNumber' are used. In fact if any (dummy) data is passed via
        # other fields the query will fail.
        self.vat_query: Dict[str, str] = {
            "countryCode": "",
            "vatNumber": "",
            "requesterMemberStateCode": "",
            "requesterNumber": "",
            "traderName": "",
            "traderStreet": "",
            "traderPostalCode": "",
            "traderCity": "",
            "traderCompanyType": ""
        }
        self.address_regex_dict: dict = {}
        self.load_address_dict()
        try:
            self.countries: list = check_eu_service_status.check_service_status()
        except RuntimeError as e:
            raise RuntimeError(f"There was an exception, {e}, connecting to the VIES status checker.")

    def load_address_dict(self):
        """
        This function has individual country address regexes for addresses retrieved from VIES.
        Each country address is unique. Some countries, e.g. DE and ES, do not return company name
        and address details, those are listed as 'None'.
        We only use company name, street address, postal code and city. Some countries, e.g. PT, return
        further address details like the municipality, these are parsed but not included in the returned
        VAT lookup result dict.
        :return:
        """
        self.address_regex_dict = {
            'AT': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'BE': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'BG': r'^(?P<street>.*),\s(?P<city>.*)\s(?P<postal_code>\d+)$',
            'CY': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'CZ': r'',
            'DE': None,
            'DK': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)\n$',
            'EE': r'^(?P<street>.*)\s{3}(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'EL': r'^(?P<street>\S+\s\w+)\s{3,}(?P<postal_code>\S+\S+)\s-\s(?P<city>.*)$',
            'ES': None,
            'FI': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'FR': r'^(?P<street>.*)\n(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'HR': r'^(?P<street>.*),\s+(?P<city>.*),\s+(?P<postal_code>.*)$',
            'HU': r'^(?P<street>.*)\s+(?P<postal_code>\d+)\s+(?P<city>.*)$',
            'IE': r'',
            'IT': r'^(?P<street>.*)\n(?P<postal_code>\d+)\s+(?P<city>.*)\s\S{2}\n$',
            'LT': r'^(?P<street>.*),\s+(?P<city>.*),\s+((?P<postal_code>LT\d{5})|(?P<province>.*))$',
            'LU': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'LV': r'^(?P<street>.*),\s+(?P<city>.*),\s+(?P<postal_code>\S+)$',
            'MT': r'',
            'NL': r'^\n(?P<street>.*)\n(?P<postal_code>\S+)\s+(?P<city>.*)\n$',
            'NO': r'',
            'PL': r'',
            'PT': r'^(?P<street>.*)\n(?P<municipality>\S+)\n(?P<postal_code>\S+)\s+(?P<city>.*)$',
            'RO': r'^(?P<street>.*)$',
            'RS': r'',
            'SE': r'^(?P<street>.*)\n(?P<postal_code>\S+\s\S+)\s+(?P<city>.*)$',
            'SI': r'^(?P<street>.*),\s+(?P<postal_code>\d{4})\s+(?P<city>.*)$',
            'SK': r'^(?P<street>.*)\n(?P<postal_code>\S+)\s(?P<city>.*)\n(?P<country>.*)$',
            'XI': r'',
        }

    # Tenacity retry decorator, number of attempts = 10, time increases exponentially
    @retry(
        reraise=True,
        retry=retry_if_exception_type(Union[requests.ConnectionError, requests.Timeout]),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def lookup_vat(self, vat_no: str, result: dict) -> dict:
        """
        Lookup VAT
        :param vat_no:
        :param result:
        :return:
        """

        self.vat_query["countryCode"] = vat_no[:2]
        self.vat_query["vatNumber"] = vat_no[2:]

        # Check country against the list self.countries which was populated at class init. We run it at class
        # init in case there are multiple lookups for EU counties. If member state service is down there is
        # no point in continuing.
        if self.vat_query["countryCode"] in self.countries:
            print(f"The VAT lookup service for member state {self.vat_query['countryCode']} is not available.")
            result['err_msg'] = (f"The VAT lookup service for member state {self.vat_query['countryCode']} "
                                 f"is not available.")
            return result

        # Member state
        json_data = json.dumps(self.vat_query)
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
            'Content-type': 'application/json',
        }
        url: str = 'https://' + self.host + self.service

        try:
            res = requests.post(url, data=json_data, headers=headers)
        # Note: Status code cannot be set as if any exceptions are raised the res object,
        # and therefore the res.status_code, cannot be known.
        # Note: Requests.HTTPError does NOT catch returned 404, and other HTTP failure results,
        # they are not considered as application level (exception) errors
        except requests.HTTPError as e:
            print(f"Invalid URL, exception = {e.response.reason}: {e.response.status_code}")
            raise requests.HTTPError(f"{e}")
        except requests.ConnectionError as e:
            print(f"Requests connection exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.ConnectionError(f"{e}")
        except requests.Timeout as e:
            print(f"Requests timeout exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.Timeout(f"{e}")
        except requests.RequestException as e:
            print(f"There was a general Requests, or supporting library, exception.\n"
                  f"Exception = {e}")
            raise requests.RequestException(f"{e}")
        except Exception as e:
            print(f"There was a general exception querying the VIES VAT lookup service.\n"
                  f"Exception = {e}")
            raise RuntimeError(f"{e}")

        # Got a connection, now check response status code
        status_code = res.status_code
        if status_code == 200:
            # # Show raw response - for analysing address regexes
            # print()
            # print(json.dumps(res.json(), ensure_ascii=False, indent=4).encode('utf-8').decode())
            # print()
            # # Show raw response - for analysing address regexes
            if res.json()['valid']:
                result['valid'] = True
                result['vat_enabled'] = True
                result['country_code'] = res.json()['countryCode']
                # Get address regex and parse address line if available
                address_regex = self.address_regex_dict[result['country_code']]
                if address_regex is not None:
                    result['company_name'] = res.json()['name']
                    try:
                        match = re.match(rf"{address_regex}", res.json()['address'])
                    except Exception as e:
                        print(f"There was an error,{e}, matching the address to the country address regex.")
                        return result
                    if match:
                        try:
                            if 'street' in match.groupdict():
                                result['street'] = match.group('street').strip()
                            if 'postal_code' in match.groupdict():
                                result['postal_code'] = match.group('postal_code').strip()
                            if 'city' in match.groupdict():
                                result['city'] = result['city'] = match.group('city').strip()
                        except IndexError as e:
                            print(f"There was an error, '{e}', parsing the address.\n"
                                  f"Is the address regex for country {result['country_code']} defined?")
                            return result
                        else:
                            result['has_details'] = True
                            print(f"Company Name: {result['company_name']}")
                            print(f"Address:")
                            print(f"\t{result['street']}")
                            print(f"\t{result['postal_code']} {result['city']}")
                            print(f"\t{result['country_code']}\n")
                else:
                    print(f"\nThe VAT number is valid — but the member state, {result['country_code']}, "
                          f"does not supply company name or address details.\n")
                # Only change ret_code from -1 to 0 if all processing is OK.
                result['ret_code'] = 0
                return result
            else:
                print(f"\nThe VAT number {vat_no} is not valid.\n")
                result['err_msg'] = "VAT number is not valid"
                return result
        elif 400 <= status_code <= 499:
            print(f"URL for VIES lookup invalid, status code: {status_code}")
            raise ConnectionError(f"URL for VIES lookup invalid, status code: {status_code}")
        elif 500 <= status_code <= 599:
            print(f"VIES server error, status code: {status_code}")
            raise ConnectionError(f"VIES server error, status code: {status_code}")
        else:
            # Otherwise some other error causing failure, ret_code changed to 1
            print(f"Other error connecting to VIES system, status code: {status_code}")
            raise ConnectionError(f"VIES server connection error, status code: {status_code}")


def main():
    vat_no = input('Enter an EU VAT number to look up: ')
    print()
    result = {
        'ret_code': -1,
        'valid': False,
        'vat_enabled': False,
        'err_msg': None,
        'has_details': False,
        'company_name': None,
        'street': None,
        'postal_code': None,
        'city': None,
        'country_code': None,
        'country': None,
    }
    try:
        lookup = LookupVat()
        res = lookup.lookup_vat(vat_no, result)
        print(res)
    except Exception as e:
        print(f"There was an exception, {e}, running the EU VAT lookup function.")


if __name__ == '__main__':
    main()
