import re
from typing import Union, Dict
import json
# Third party
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# Application
from vat_utils import get_country_name_from_code


class LookupVat:
    def __init__(self) -> None:
        self.host = 'ec.europa.eu'
        self.service = '/taxation_customs/vies/rest-api/check-vat-number'
        self.country_codes: dict = get_country_name_from_code()
        self.vat_query: Dict[str, str,] = {
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
            'RO': None,
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
            print(f"There was a general exception querying the GB VAT lookup service.\n"
                  f"Exception = {e}")
            raise RuntimeError(f"{e}")

        # Got a connection, now check response status code
        status_code = res.status_code
        if status_code == 200:
            # # Show raw response
            # print()
            # print(json.dumps(res.json(), indent=4))
            # print()
            # # Show raw response
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
                        print(f"There was an error = {e}.")
                        return result
                    if match:
                        try:
                            if match.group('street'):
                                result['street'] = match.group('street').strip()
                            if match.group('postal_code'):
                                result['postal_code'] = match.group('postal_code').strip()
                            if match.group('city'):
                                result['city'] = match.group('city').strip()
                        except IndexError as e:
                            print(f"There was an error, '{e}', parsing the address.\n"
                                  f"Is the address regex for country {result['country_code']} defined?")
                            return result
                        else:
                            result['has_details'] = True
                            print(f"\nCompany Name: {result['company_name']}")
                            print(f"Address:")
                            print(f"\t{result['street']}")
                            print(f"\t{result['postal_code']} {result['city']}")
                            print(f"\t{result['country_code']}\n")
                else:
                    print(f"The member state {result['country_code']} does not supply company name or address details.")
                # Only change ret_code from -1 to 0 if all processing is OK.
                result['ret_code'] = 0
                return result
            else:
                print(f"The VAT number {vat_no} is not valid")
                return result
        elif 400 <= status_code <= 499:
            # 404 is the defined return code for successful connection but VAT number not found,
            # so we return unchanged ret_code = -1
            print(f"Status code: {status_code}")
            print(f"URL invalid")
            return result
        elif 500 <= status_code <= 599:
            print(f"Status code: {status_code}")
            print(f"Server error")
            return result
        else:
            # Otherwise some other error causing failure, ret_code changed to 1
            print(f"Status code: {status_code}")
            print(f"The lookup process for {vat_no} failed, likely invalid data.")
            return result


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
