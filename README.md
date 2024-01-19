# European VAT Checker

## Introduction
This is a pure Python VAT number validator and company & address information for most European country VAT numbers. It includes EU member states for which there is one API service, VIES, which links to the national VAT number lookup system of the respective EU countries, as well as other non-EU European countries such as the UK, Switzerland, Norway.

It is only for European countries.

It was developed as a specific VAT number checking functionality of a larger system and can be utilised as such — passing a VAT number and returning a Python dictionary of resultant data — or as an interactive tool.  

## Functionality
The system provides: 

1. Simple (initial) verification by checking a submitted VAT number against a regex of the country's VAT number format.
2. If the submitted VAT number passes initial verification it is then checked for validity with (existence in) the relevant online VAT number checking service (API). If a service is unavailable the VAT check will terminate. In most cases VatCheck will confirm that a country's VAT service is available before doing a live lookup of the VAT number. 
3. It checks (using data returned by online services) whether a VAT number is actually valid for VAT purposes — in some (few) cases a what is stated as a VAT number may be a valid national ID but not be enabled for VAT purposes. The system also, for most countries, returns the company name and address. Please note: some countries, for example Germany and Spain, *do not return any information about the company*, including the company name. In such cases VatCheck will print a notification.
4. Addresses returned are parsed wherever possible into street, postal code, city and country using address format regexes. For EU countries returned via the VIES service which have differently formatted address strings there is a regex for each country which parses the address — see `self.address_regex_dict` in `check_eu_vat.py`. Address parsing is not possible for UK addresses due to, well, UK addresses.    

## New VIES REST Service
VIES has implemented a new service using REST instead of SOAP, this should be an improvement over the previous SOAP service. The VatCheck system now uses the new REST API. 

VIES also has a new REST service which returns the availability of the VAT lookup service for all member states. This is queried during instantiation of the EU VAT class and a list of unavailable states returned as a list. During lookups of EU VAT numbers the member state is checked against the unavailable countries list and, if found, the VAT lookup is cancelled. 

## Install
Clone the GitHub repository, it is assumed that Python best practices are followed and that the application will run in a virtual environment. The pyproject.toml file lists all required dependencies and Python version. 

## Usage
Can be either as an included module of a larger application (in which case it should be added to the other application as required) or as a stand-alone utility.

Assuming the module `vat_checker` has been added correctly into an existing application it can be called as follows: 

```python
import vat_checker

check = vat_checker.CheckVat()

vat_no = "XX1234567890"
result = check.do_lookup(vat_no)
```
The returned variable 'result' is a Python dictionary which is initialised as below:

```python
self.result = {
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
```
The returned dict contains more information than just whether a VAT number is verified against the relevant service. Wherever possible the address is parsed into usable fields that can be queried. 

If using as an interactive utility run the Python script `vat_checker.py` and provide a VAT number at the prompt.
