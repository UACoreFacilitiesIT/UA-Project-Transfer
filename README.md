# UA-Project-Transfer

Transfers service requests from Agilent's iLab software to Illumina's Clarity LIMS software.

## Motivation

To transfer service requests from iLab to Clarity LIMS programmatically.

## Features

- Creates projects in Clarity LIMS based on corresponding iLab service requests.
- Route samples to the correct workflow in Clarity LIMS.
- Validates service request prices.
- If the transfer fails at any point in sample creation, there will not be side effects of project transfer.

## Installation

```bash
git clone https://github.com/UACoreFacilitiesIT/UA-Project-Transfer.git
```

## Code Example

```bash
cd UA-Project-Transfer/ua_project_transfer
python project_transfer.py --ilab {iLab environment} --lims {LIMS environment}
```

## Tests

```bash
cd UA-Project-Transfer/ua_project_transfer/tests
nosetests test_project_lims_tools.py
```

## How to Use

To use project_transfer with default settings in your environment, you will need to make a few changes:

#### Environment changes

- Add a file named "lims_token.json" in the form of:
  - {
    "host": "{api_endpoint(https://.*v2/)}",
    "username" : "{api_creds_username)",
    "password" : "{api_creds_password}"
    }

- Add a file named "ilab_token.json" in the form of:
  - {
    "token": "{ilab_api_token}",
    "core_id": "{ilab_core_id}"
    }
</br>
- If you want to customize logging, run monitoring, or credential harvesting, create a "core_specifics.py" file with that code. Otherwise, save the "core_specifics_template.py" file as "core_specifics.py".

  - To customize logging:
        Either save the "log_config_template.py" as "log_config.py" OR create a custom log_config file, including at least what is in the template file.

  - To customize run monitoring:
        Add the setup for whichever software monitoring you decide to use. Can be left blank if no monitoring is desired.

  - To customize credential harvesting:
        Either use what is written in the template, utilizing the two token files you just created. OR delete those two token files and implement your own credential harvesting method.

  - The wf_locations dictionary must also be updated to map the iLab
        Form names to their respective next_steps functions.

  - The unroutable_forms list must be updated to contain any iLab Form names
        you want to skip.

#### Clarity changes

- The UDF's in either the custom form's grid or fields with _each_sample in their identifiers must be exactly the name of the target Clarity UDF.

- A sample's container type's name must map exactly to a container type's name in Clarity.

- Workflows can only have samples routed to them if they are active.

- WF_STEPS in wf_steps.py must hold the mappings of conditions to a tuple containing (the workflow, the step name).

#### iLab changes

- The code that interprets service requests (ua_ilab_tools) has a few requirements with you iLab setup:
</br>

- **Sample specific changes (sample grid)**:

  - The information for samples must be stored in a "grid" custom form data type.

  - The first column of that grid will be interpreted as the sample names.

  - Any text added to this grid will have it's input scrubbed so that it matches r"[^a-zA-Z0-9:,.+]", where '+' is replaced with "plus", and is encoded as ascii -- special characters are converted using
    `unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")`

  - If a form is set up with 96-well plate(s) as the form's container type (see below how to set a form's container type), the it must have the column name of "Well Location".

    - The formats that are allowed in the "Well Location" column are A:1, H12, B09, or C:09 (of course including A-H and 1-12).

  - If a UDF is of the "numeric" type in Clarity, add that UDF identifier (the column name in the grid or the .*_each_sample form field identifier) to extract_custom_forms.py's ONLY_INT_FIELDS.

  - Similarly, anything that is set as a "Toggle Switch" UDF in CLarity should be added to extract_custom_forms.py's BOOL_FIELDS.

</br>

- **Price Check specific changes**:

  - You will need to define the quantity of each unit of a charge in price_check.py's unit_definitions (e.g. {"each": 1, "prep":11}).

</br>

- **Form specific changes**:

  - Custom forms with names that match the pattern in ua_ilab_tools' SKIP_FORM_PATTERNS will not be evaluated.

    - You **can** have a service request with a skipped form and a not skipped form, and the request will transfer.

    - Each service request can only have one form that has sample information.

    - Any custom form fields that end with "_each_sample" will be applied to every sample in the form.
      - For example, if your Clarity environment had the UDF "Concentration", and you wanted a single concentration value to be added to every sample within a form's sample grid, the identifier for that field in the custom form's iLab setup should say "Concentration_each_sample".
      - These identifiers must be exactly the name of the UDF in Clarity, before the "_each_sample" portion.

  - The container type of the form is determined by whether:
    - There's a grid column named "Container Name" (multiple 96-well plates)
    - There's a custom form field with the identifier of container_name (single 96-well plate)
    - Else, the container type is a Tube

  - If you need to add more container types or change these rules, you can do so by editing the .*_bind functions, and updating the con_strategy dict() in bind_container_info() in extract_custom_forms.py.

  - Each form must have only 1 container type.

  - Duplicate location values are handled based on the container type of the form. The rules for what is allowed are:

Container Type | Duplicate Names Allowed | Duplicate Wells Allowed
:---: | :---: | :---:
Tube | :x: | Always 1:1
96 Well Plate | :heavy_check_mark: | :x:

## Credits

[sterns1](https://github.com/sterns1)
[raflopjr](https://github.com/raflopjr)
[RyanJohannesBland](https://github.com/RyanJohannesBland)
[EtienneThompson](https://github.com/EtienneThompson)

## License

MIT
