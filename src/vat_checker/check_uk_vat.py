# import json
from time import sleep
from typing import Union
# Third party
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# Application
from vat_utils import get_country_name_from_code


class LookupVat:
    def __init__(self) -> None:
        self.host = 'api.service.hmrc.gov.uk'
        self.service = '/organisations/vat/check-vat-number/lookup/'
        # result: dict = {}
        self.country_codes: dict = get_country_name_from_code()

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

        country_code = vat_no[:2]
        company_number = vat_no[2:]

        if country_code != 'GB':
            print(f"Country code {country_code} of vat number {vat_no} is not valid for this service.")
            result['err_msg'] = f"Country code {country_code} of vat number {vat_no} is not " \
                                f"valid for this service."
            return result

        headers = {
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
            "Accept": "application/vnd.hmrc.1.0+json"
        }
        url: str = 'https://' + self.host + self.service + company_number
        # Service is rated limited, put in a delay of 300 ms so impossible to exceed (very low) rate limit
        # of 3 lookups/sec
        sleep(.3)

        try:
            res = requests.get(url, headers=headers)
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
            # # Testing - show raw response
            # print()
            # print(json.dumps(res.json(), indent=4))
            # print()
            # # Testing - show raw response
            result['ret_code'] = 0
            result['valid'] = True
            result['vat_enabled'] = True
            if 'name' in res.json()['target']:
                result['company_name'] = res.json()['target']['name']
            # We have address key with values
            if 'address' in res.json()['target'] and len(res.json()['target']['address']) != 0:
                result['has_details'] = True
                # Make a dictionary from the JSON
                address: dict = res.json()['target']['address']
                street: str = ''
                # UK addresses are messy, parse address lines, including city, as street.
                # Unfortunately it is *almost impossible* to get the city out as a separate value.
                for address, address_line in address.items():
                    if address[:4] == 'line':
                        street = street + address_line + '\n'
                if street:
                    # Remove last new line character
                    street = street[:-1]
                result['street'] = street
                if 'postcode' in res.json()['target']['address']:
                    result['postal_code'] = res.json()['target']['address']['postcode']
                if 'countryCode' in res.json()['target']['address']:
                    result['country_code'] = res.json()['target']['address']['countryCode']
                    if result['country_code'] in self.country_codes:
                        result['country'] = self.country_codes[result['country_code']]

            # Print the result
            print(f"VAT number {vat_no} is valid, company data:")
            print(result['company_name'])
            print(result['street'])
            print(result['postal_code'])
            print(result['country'])
            print()
            return result
        elif status_code == 404:
            # 404 is the defined return code for successful connection but VAT number not found,
            # so we return unchanged ret_code = -1
            print(f"Status code: {status_code}")
            print(f"VAT number {vat_no} is not valid.")
            return result
        else:
            # Otherwise some other error causing failure, ret_code changed to 1
            print(f"Status code: {status_code}")
            print(f"The lookup process for {vat_no} failed, likely invalid data.")
            return result


def main():
    vat_no = input('Enter a UK VAT number to look up: ')
    print()
    try:
        lookup = LookupVat()
        res = lookup.lookup_vat(vat_no)
        print(res)
    except Exception as e:
        print(f"There was an exception, {e}, running the UK VAT lookup function.")


if __name__ == '__main__':
    main()
