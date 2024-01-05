import json
from typing import Union
# Third party
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# Application


class LookupVat:
    def __init__(self) -> None:
        self.host = 'data.brreg.no'
        self.service = '/enhetsregisteret/api/enheter/'
        self.service_check = '/enhetsregisteret/api/'

    @retry(
        reraise=True,
        retry=retry_if_exception_type(Union[requests.ConnectionError, requests.Timeout]),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def connect(self):
        url = 'https://' + self.host + self.service_check
        with requests.Session() as ses:
            try:
                print("Connecting to Norwegian government VAT lookup web service...")
                res = ses.get(url)
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

            status_code = res.status_code
            if status_code == 200:
                print(f"...connection successful.")
            else:
                raise RuntimeError(f"Connection unsuccessful, response code {status_code}")

    # Tenacity decorator, number of attempts = 10, time increasing exponentially
    @retry(
        reraise=True,
        retry=retry_if_exception_type(Union[requests.ConnectionError, requests.Timeout]),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def lookup_vat(self, vat_no: str, result: dict) -> dict:
        """
        Lookup VAT number
        :param vat_no:
        :param result:
        :return:
        """

        country_code = vat_no[:2]
        company_number = vat_no[2:]

        if country_code != 'NO':
            print(f"Country code {country_code} of vat number {vat_no} is not valid for this service.")
            return result

        url = 'https://' + self.host + self.service + company_number
        with requests.Session() as ses:
            try:
                res = ses.get(url)
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

            # Got a connection, now check response status code
            status_code = res.status_code
            if status_code == 200:
                result['ret_code'] = 0
                result['valid'] = True
                data = json.loads(res.text)
                print(f"Company exists in Norwegian company register.")
                result['organisation_no'] = data['organisasjonsnummer']
                result['company_name'] = data['navn']
                result['vat_no'] = vat_no
                print(f"Norwegian Organisation Number: {result['organisation_no']}")
                if 'registrertIMvaregisteret' in data:
                    print(f"VAT Number: {result['vat_no']} is VAT enabled.")
                    result['vat_enabled'] = True
                else:
                    print(f"Company number {result['organisation_no']} is not VAT enabled.")
                print(f"Company Name: {result['company_name']}")
                if 'forretningsadresse' in data:
                    result['has_details'] = True
                    result['street'] = ','.join(data['forretningsadresse']['adresse'])
                    result['city'] = data['forretningsadresse']['poststed']
                    result['postal_code'] = data['forretningsadresse']['postnummer']
                    result['country_code'] = data['forretningsadresse']['landkode']
                    print(f"Address:")
                    print(f"\t{result['street']}")
                    print(f"\t{result['postal_code']} {result['city']}")
                    print(f"\t{result['country_code']}")
                return result
            # URL was not found, this means the ID provided (part of the URL) does not exist.
            # No point in processing further.
            elif status_code == 404:
                print('Company ID does not exist in register.')
                result['err_msg'] = 'Company ID does not exist in register'
                return result
            else:
                result['err_msg'] = 'Unknown error'
                return result


def main():
    vat_no = input('Enter a Norwegian VAT number to look up: ')
    print()
    lookup = LookupVat()
    res = lookup.lookup_vat(vat_no)
    print(res)


if __name__ == '__main__':
    main()
