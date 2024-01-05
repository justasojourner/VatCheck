# Standard library
from typing import Optional
# Third party
import zeep
import zeep.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
import requests


class LookupVat:
    def __init__(self) -> None:
        self.settings = zeep.Settings(
            strict=False,
            xml_huge_tree=True,
            extra_http_headers={'keep_alive': 'False'},
        )
        self.wdsl = 'https://www.uid-wse-a.admin.ch/V5.0/PublicServices.svc?wsdl'
        self.client: Optional[zeep.Client] = None
        self.valid_uid: bool = False

    # Number of attempts = 10
    @retry(
        reraise=True,
        retry=retry_if_not_exception_type(requests.HTTPError),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=20),
    )
    def connect(self):
        """
        Connect to Swiss government web service.
        :return: Nothing, the class attribute 'self.client' will be set.
        """
        print("Connecting to Swiss government VAT lookup web service...")
        try:
            self.client = zeep.Client(self.wdsl, settings=self.settings)
        # If the URL is invalid no point in retrying
        except requests.HTTPError as e:
            print(f"Invalid URL, exception = {e.response.reason}: {e.response.status_code}")
            raise requests.HTTPError(f"{e}")
        except requests.ConnectionError as e:
            print(f"Requests connection exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.ConnectionError(f"{e}")
        # This will catch both connect and read timeout exceptions
        except requests.Timeout as e:
            print(f"Requests timeout exception, retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.Timeout(f"{e}")
        except requests.RequestException as e:
            print(f"There was a general Requests, or supporting library, exception. Retry will be attempted.\n"
                  f"Exception = {e}")
            raise requests.RequestException(f"{e}")
        except Exception as e:
            print(f"There was a general exception which may also be a Zeep error, retry will be attempted.\n"
                  f"Exception = {e}")
            raise Exception(f"{e}")
        else:
            print(f"...connection successful.\n")

    # Number of attempts = 5
    @retry(
        reraise=True,
        retry=retry_if_not_exception_type((zeep.exceptions.Fault, UnboundLocalError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, max=20)
    )
    def lookup_vat(self, vat_no: str, result: dict, validate_only: bool = False) -> dict:
        """
        This function does a lookup of a Swiss VAT number.

        :param vat_no:
        :param result:
        :param validate_only:
        :return: The class result dictionary
        """

        # Do simple validation first, this will still return the result dictionary
        # with only the relevant keys filled in.
        # This will use Tenacity for multiple attempts
        try:
            if self.client is not None:
                self.valid_uid = self.client.service.ValidateUID(vat_no)
            else:
                raise UnboundLocalError
        # This shouldn't ever occur if the Zeep client object had been properly initialised.
        # This will not do a Tenacity retry, see @retry decorator above, it will return to check_vat.py
        # which will terminate the program.
        except UnboundLocalError:
            raise UnboundLocalError(f"Program error, self.client attribute has not been assigned before use")
        # If there is a Zeep exception it is likely to be an *invalid* VAT number, which is different from
        # a *failed* VAT number lookup, we need to test both.
        # The 'zeep.exceptions.Fault' exception will not retry - if Zeep gets an exception here it means
        # it was able to connect, and it got back an explicit client failure. So no sense in retrying.
        except zeep.exceptions.Fault as e:
            result['err_msg'] = f"Zeep exception: {e}"
            return result
        # Others, catch-all.
        except Exception as e:
            result['err_msg'] = f"General exception: {e}"
            return result

        # There was a response (a connection) from the web services server, that is 'self.valid_uid'
        # is no longer None, as initialised in __init__, but is it true or false?
        # This is needed as well as the Zeep client exception testing above.
        # Was _explicitly_ set to False by web service?
        if self.valid_uid is True:
            result['ret_code'] = 0
            result['valid'] = True
            result['vat_enabled'] = True
        # Was _explicitly_ set to False by web service?
        elif self.valid_uid is False:
            # result['valid'] will be False from init of dict, but just to be safe...
            result['valid'] = False
            result['err_msg'] = f"The UID number, {vat_no}, is not a valid VAT number. " \
                                f"The number may exist, but not be of type VAT."
            # It failed, no need to continue regardless of whether validate_only or not.
            return result
        # We _really_ shouldn't get here... but just in case.
        else:
            result['valid'] = False
            result['err_msg'] = f"There was an unexpected error looking up VAT number, {vat_no}."
            return result

        # If it was just a simple validation then end and return at this point. Most keys in the result
        # dict will remain unchanged, result['valid'] has been set to True above.
        if validate_only:
            return result

        # If not a simple validation run second query to get details, the 'valid' dict key will
        # already have been set.
        try:
            # We shouldn't be here if the Zeep client object has not been initialised
            if self.client is not None:
                # Query is a dict, a dict (inside a list) is returned
                query_dict = {'uidOrganisationIdCategorie': vat_no[:3], 'uidOrganisationId': vat_no[3:]}
                response = self.client.service.GetByUID(query_dict)
            else:
                raise UnboundLocalError
        except UnboundLocalError:
            raise UnboundLocalError(f"Program error, self.client attribute has not been assigned before use")
        # TODO - this needs to be tested and clarified
        # If the data is restricted then the web service returns a client fault exception,
        # this is really not ideal therefore I need to do a workaround here
        except zeep.exceptions.Fault as e:
            # The VAT number is valid, so we should not unset the result['valid'] key here,
            # the 'has_details' key will stay as False
            result['err_msg'] = f"There was a lookup error, {e}, trying to look up " \
                                f"the details of the UID/VAT number {vat_no}."
            raise zeep.exceptions.Fault(f"{e}")
        except Exception as e:
            result['err_msg'] = f"There was a general error, {e} trying to look up " \
                                f"the details of the UID/VAT number {vat_no}."
            raise Exception(f"{e}")

        # Extract all the desired data from the complicated dictionary
        if response is not None:
            # Things can break here, put everything in an Exception block
            try:
                if response[0]['organisation']['organisationIdentification']['organisationAdditionalName']:
                    result['company_name'] = \
                        response[0]['organisation']['organisationIdentification']['organisationAdditionalName']
                else:
                    result['company_name'] = \
                        response[0]['organisation']['organisationIdentification']['organisationName']
                if response[0]['organisation']['address'][0]['street']:
                    street = response[0]['organisation']['address'][0]['street']
                else:
                    street = ''
                if response[0]['organisation']['address'][0]['houseNumber']:
                    house_number = response[0]['organisation']['address'][0]['houseNumber']
                else:
                    house_number = ''
                result['street'] = (street + ' ' + house_number).strip()
                if response[0]['organisation']['address'][0]['town']:
                    result['city'] = \
                        response[0]['organisation']['address'][0]['town']
                if response[0]['organisation']['address'][0]['countryIdISO2']:
                    result['country_code'] = \
                        response[0]['organisation']['address'][0]['countryIdISO2']
                if 'swissZipCode' in response[0]['organisation']['address'][0]['_value_1'][0]:
                    result['postal_code'] = \
                        response[0]['organisation']['address'][0]['_value_1'][0]['swissZipCode']
                elif 'foreignZipCode' in response[0]['organisation']['address'][0]['_value_1'][0]:
                    result['postal_code'] = \
                        response[0]['organisation']['address'][0]['_value_1'][0]['foreignZipCode']
                print(f"\nCompany Name: {result['company_name']}")
                print(f"Address:")
                print(f"\t{result['street']}")
                print(f"\t{result['postal_code']} {result['city']}")
                print(f"\t{result['country_code']}\n")
                result['has_details'] = True
            except Exception as e:
                print(f"Address details lookup failed, reason {e}")
                result['err_msg'] = f"There was an error, '{e}' trying to parse the " \
                                    f"address details for {vat_no}."
        else:
            # No data in response? In that case the following dictionary keys are returned:
            # 'valid' = True, 'err_msg', 'country' & 'has_details' = False
            # Cannot get country code from the details' lookup, fall back to country in VAT no.
            result['country_code'] = vat_no[:2].upper()
            result['err_msg'] = f"The VAT/UID number {vat_no} is valid, but the company details are withheld."
        return result
