# NOTE: These tests WILL have side effects in your environment; be sure to run
# them on a developer instance.

import os
import json
import time
import unittest
import requests
from datetime import datetime
from jinja2 import Template
from nose.tools import raises
from nose.plugins.attrib import attr
from bs4 import BeautifulSoup
from ua_ilab_tools import api_types
from ua_project_transfer import project_lims_tools


LIMS_API = None
LIMS_UTIL = None
DEFAULT_RES = None


def setUpModule():
    creds_path = (os.path.join(
        os.path.split(__file__)[0], "lims_dev_token.json"))
    with open(creds_path, 'r') as file:
        creds = json.load(file)

    global LIMS_API
    global LIMS_UTIL
    global DEFAULT_RES

    LIMS_API = project_lims_tools.ProjectLimsApi(
        host=creds["host"],
        username=creds["username"],
        password=creds["password"])
    LIMS_UTIL = project_lims_tools.LimsUtility(
        host=creds["host"],
        username=creds["username"],
        password=creds["password"])

    DEFAULT_RES = api_types.Researcher(
        "System",
        "Administrator",
        "internal",
        "",
        f"{LIMS_API.tools.api.host}researchers/1")

    assert LIMS_API is not None
    assert LIMS_UTIL is not None


class TestProjectLimsTools(unittest.TestCase):
    @attr("researcher")
    def test_get_researcher_uri_with_one_and_two_existing_researchers(self):
        current_time = datetime.now()

        res = api_types.Researcher(
            f"Test-{current_time}",
            "Last Name",
            f"{LIMS_API.tools.api.host}labs/1",
            "TEST@email.arizona.edu",
            "")

        uri_answer = BeautifulSoup(_post_researcher(current_time), "xml")
        uri_answer = uri_answer.find("res:researcher")["uri"]

        assert len(LIMS_API.get_researcher_uri(res)) == 1
        assert LIMS_API.get_researcher_uri(res) == [uri_answer]

        uri_answer = BeautifulSoup(_post_researcher(current_time), "xml")
        uri_answer = uri_answer.find("res:researcher")["uri"]

        assert len(LIMS_API.get_researcher_uri(res)) == 2

    @attr("researcher")
    def test_get_researcher_uri_with_non_existing_researcher(self):
        res = api_types.Researcher(
            "TEST_NOT",
            "_PRESENT",
            "internal",
            "TEST@email.arizona.edu",
            "")
        assert len(LIMS_API.get_researcher_uri(res)) == 0

    @attr("researcher")
    def test_post_researcher(self):
        current_time = str(datetime.now())
        res = api_types.Researcher(
            f"Researcher_TEST_{current_time}",
            "POST_TEST",
            "internal",
            "Test@email.arizona.edu",
            "")
        result_uri = LIMS_API.post_researcher(res)

        res_soup = BeautifulSoup(
            LIMS_API.tools.api.get(result_uri), "xml")
        res_soup = res_soup.find("res:researcher")

        assert result_uri is not None
        assert current_time in res_soup.find("first-name").text

    @attr("researcher")
    @raises(project_lims_tools.POSTNameCollision)
    def test_post_researcher_already_in_system(self):
        res = api_types.Researcher(
            "Already_In",
            "System",
            "internal",
            "Test@email.arizona.edu",
            "")
        LIMS_API.post_researcher(res)
        LIMS_API.post_researcher(res)

    @attr("project")
    def test_post_project(self):
        prj = api_types.Project(
            f"Project_TEST_{datetime.now()}",
            DEFAULT_RES,
            str(datetime.today().date()),
            [],
            "")
        result_uri = LIMS_API.post_project(prj)

        assert result_uri is not None

    @attr("project")
    @raises(project_lims_tools.POSTNameCollision)
    def test_post_project_already_in_system(self):
        prj = api_types.Project(
            "Already_in_system",
            DEFAULT_RES,
            str(datetime.today().date()),
            [],
            "")
        LIMS_API.post_project(prj)
        LIMS_API.post_project(prj)

    @attr("container")
    def test_batch_post_containers(self):
        current_time = []
        sample_list = []
        for x in range(5):
            current_time.append(datetime.now().__str__())
            time.sleep(.1)
            sample = api_types.Sample("Test_{}".format(current_time[x]))
            sample.con = api_types.Container(
                "Test_{}".format(current_time[x]), "96 well plate", "", "")
            sample_list.append(sample)

        result = LIMS_API.batch_post_containers(
            sample_list, "Stephen_Test")

        for link in result:
            assert link is not None

    @attr("container")
    def test_batch_post_container_already_in_system(self):
        sample_list = []
        current_time = str(datetime.now().date())
        current_time_name = f"Test_{current_time}"
        for _ in range(2):
            sample = api_types.Sample(current_time_name)
            sample.con = api_types.Container(
                current_time_name, "96 well plate", "", "")
            sample_list.append(sample)

        result = LIMS_API.batch_post_containers(
            sample_list, "Stephen_Test")

        for link in result:
            con_soup = BeautifulSoup(LIMS_API.tools.api.get(link), "xml")
            con_name = str(con_soup.find("name"))
            assert f"Test_{current_time}" in con_name

    @attr("sample")
    def test_batch_post_samples(self):
        prj_info = _post_project()
        samples = _generate_samples()

        result_uris = LIMS_API.batch_post_samples(samples, prj_info)
        smp_soups = BeautifulSoup(
            LIMS_API.tools.api.get(result_uris), "xml")

        for smp_soup in smp_soups.find_all("smp:sample"):
            smp_uri = smp_soup["uri"]
            assert smp_uri is not None

    @attr("sample")
    def test_batch_post_samples_ampersand_udf_name_and_value(self):
        # NOTE: Replace this UDF with another that has an '&' in its name in
        # your test environment.
        sample_data_table = {"udf_H&E Slide received?": "true"}
        prj_info = _post_project()
        samples = _generate_samples(sample_data_table)

        result_uris = LIMS_API.batch_post_samples(samples, prj_info)
        smp_soups = BeautifulSoup(
            LIMS_API.tools.api.get(result_uris), "xml")

        for smp_soup in smp_soups.find_all("smp:sample"):
            smp_uri = smp_soup["uri"]
            # NOTE: Replace this UDF with another that has an '&' in its name
            # in test environment.
            udf_tag = smp_soup.find(
                "udf:field", attrs={"name": "H&E Slide received?"})
            assert smp_uri is not None
            assert udf_tag is not None
            assert udf_tag.text == "true"

    @attr("sample")
    def test_batch_post_samples_with_adapter_information(self):
        sample_data_table = {"adapter": "N100 (GCAAATGC)"}
        prj_info = _post_project()
        samples = _generate_samples(sample_data_table)

        result_uris = LIMS_API.batch_post_samples(samples, prj_info)
        smp_soups = BeautifulSoup(
            LIMS_API.tools.api.get(result_uris), "xml")
        art_uris = list()
        for soup in smp_soups.find_all("smp:sample"):
            art_uri = soup.find("artifact")["uri"].split('?')[0]
            art_uris.append(art_uri)

        art_soups = BeautifulSoup(
            LIMS_API.tools.api.get(art_uris), "xml")

        for art_soup in art_soups.find_all("art:artifact"):
            adapter_tag = art_soup.find("reagent-label")
            assert adapter_tag is not None
            assert adapter_tag["name"] == "N100 (GCAAATGC)"

    @attr("sample")
    def test_batch_post_samples_with_not_real_udf_data(self):
        sample_data_table = {"udf_FAKE_UDF": "FAKE", "udf_FAKE_UDF_2": "FAKE"}
        prj_info = _post_project()
        samples = _generate_samples(sample_data_table)

        result_uris = LIMS_API.batch_post_samples(samples, prj_info)
        smp_soups = BeautifulSoup(
            LIMS_API.tools.api.get(result_uris), "xml")

        for smp_soup in smp_soups.find_all("smp:sample"):
            udf_tag = smp_soup.find(
                "udf:field", attrs={"name": "FAKE_UDF"})
            assert udf_tag is None
            udf_tag = smp_soup.find(
                "udf:field", attrs={"name": "FAKE_UDF_2"})
            assert udf_tag is None

    @attr("sample")
    @raises(requests.exceptions.HTTPError)
    def test_batch_post_samples_already_in_system(self):
        prj_info = _post_project()

        con_name = f"Auto_Sample_Test_{datetime.now()}"
        con_result_soup = BeautifulSoup(_post_con(con_name), "xml")
        con_uri = con_result_soup.find("con:container")["uri"]

        sample = api_types.Sample("repeat_test")
        sample.con = api_types.Container(con_name, "", "", con_uri)
        sample.location = "A:1"
        LIMS_API.batch_post_samples([sample], prj_info)
        LIMS_API.batch_post_samples([sample], prj_info)


class TestLimsUtility(unittest.TestCase):
    def test_create_researcher_not_in_system(self):
        current_time = str(datetime.now())
        res = api_types.Researcher(
            f"Researcher_TEST_{current_time}",
            "POST_TEST",
            "internal",
            "Test@email.arizona.edu",
            "")

        prj = api_types.Project(
            f"Project_TEST_{current_time}",
            res,
            str(datetime.today().date()),
            [],
            "")

        res_uri = LIMS_UTIL.create_researcher(0000, prj)
        assert res_uri is not None

        res_soup = BeautifulSoup(LIMS_API.tools.api.get(res_uri), "xml")
        res_soup = res_soup.find("res:researcher")

        assert current_time in res_soup.find("first-name").text

    def test_create_researcher_already_in_system(self):
        current_time = str(datetime.now())
        res = api_types.Researcher(
            f"Researcher_TEST_{current_time}",
            "POST_TEST",
            "internal",
            "Test@email.arizona.edu",
            "")

        prj = api_types.Project(
            f"Project_TEST_{current_time}",
            res,
            str(datetime.today().date()),
            [],
            "")

        res_one_uri = LIMS_UTIL.create_researcher(0000, prj)
        assert res_one_uri is not None

        res_soup = BeautifulSoup(LIMS_API.tools.api.get(res_one_uri), "xml")
        res_soup = res_soup.find("res:researcher")
        assert current_time in res_soup.find("first-name").text

        res_two_uri = LIMS_UTIL.create_researcher(0000, prj)
        assert res_two_uri == res_one_uri

    def test_create_project_not_in_system(self):
        current_time = str(datetime.now())
        prj = api_types.Project(
            f"Project_TEST_{current_time}",
            DEFAULT_RES,
            str(datetime.today().date()),
            [],
            "")

        prj_uri = LIMS_UTIL.create_project(0000, prj)
        assert prj_uri != ""

        prj_soup = BeautifulSoup(LIMS_API.tools.api.get(prj_uri), "xml")
        prj_soup = prj_soup.find("prj:project")

        assert current_time in prj_soup.find("name").text

    @raises(project_lims_tools.POSTNameCollision)
    def test_create_project_already_in_system(self):
        current_time = str(datetime.now())
        prj = api_types.Project(
            f"Project_TEST_{current_time}",
            DEFAULT_RES,
            str(datetime.today().date()),
            [],
            "")

        prj_uri = LIMS_UTIL.create_project(0000, prj)
        assert prj != ""

        prj_soup = BeautifulSoup(LIMS_API.tools.api.get(prj_uri), "xml")
        prj_soup = prj_soup.find("prj:project")

        assert current_time in prj_soup.find("name").text

        prj_uri = LIMS_UTIL.create_project(0000, prj)

    def test_create_containers(self):
        current_time = str(datetime.now())
        prj = api_types.Project(
            f"Project_TEST_{current_time}",
            DEFAULT_RES,
            str(datetime.today().date()),
            [],
            "")

        custom_form = api_types.CustomForm(
            f"TEST_{current_time}",
            "0000",
            "0000")

        current_time = []
        sample_list = []
        for x in range(5):
            current_time.append(datetime.now().__str__())
            time.sleep(.1)
            sample = api_types.Sample("Test_{}".format(current_time[x]))
            sample.con = api_types.Container(
                "Test_{}".format(current_time[x]), "96 well plate", "", "")
            sample_list.append(sample)
        custom_form.samples = sample_list

        con_uris = LIMS_UTIL.create_containers(0000, prj, custom_form)
        assert con_uris is not None

        cons_soup = BeautifulSoup(LIMS_API.tools.api.get(con_uris), "xml")
        cons_soup = cons_soup.find_all("con:container")
        con_names = [con_soup.find("name") for con_soup in cons_soup]

        for i, con_name in enumerate(con_names):
            assert con_name.text.split("_")[-1] in current_time

    def test_create_samples(self):
        current_time = str(datetime.now())
        prj = _post_project()
        samples = _generate_samples()

        custom_form = api_types.CustomForm(
            f"TEST_{current_time}",
            "0000",
            "0000"
        )
        custom_form.samples = samples

        smp_uris = LIMS_UTIL.create_samples(0000, prj, custom_form)
        assert smp_uris is not None

        smps_soup = BeautifulSoup(LIMS_API.tools.api.get(smp_uris), "xml")
        smps_soup = smps_soup.find_all("smp:sample")
        smp_names = [smp_soup.find("name").text for smp_soup in smps_soup]

        for name in smp_names:
            assert "test" in name

    def test_route_strategy(self):
        prj = _post_project()
        samples = _generate_samples()

        custom_form = api_types.CustomForm(
            "RNA Extraction",
            "0000",
            "0000"
        )
        custom_form.samples = samples
        custom_form.field_to_values["Sample_Type_each_sample"] = "Test"

        # Use LIMS_API rather than LIMS_UTIL to restrict test to one function.
        smp_uris = LIMS_API.batch_post_samples(samples, prj)
        assert smp_uris is not None

        smp_art_uris = LIMS_API.tools.get_arts_from_samples(smp_uris)
        assert smp_art_uris is not None

        art_uris = [smp_art_uris[smp_uri] for smp_uri in smp_art_uris.keys()]
        assert art_uris is not None

        # NOTE: Refactor route_strategy to your own workflows, and
        # correspondingly change the call to step_router to unassign from
        # that workflow.
        LIMS_UTIL.route_strategy(art_uris, custom_form, "dev")
        LIMS_API.tools.step_router(
            "RNA Extraction",
            "Sort Extraction Samples RNA",
            art_uris,
            action="unassign")

    def test_route_strategy_unroutable_form(self):
        prj = _post_project()
        samples = _generate_samples()

        custom_form = api_types.CustomForm(
            "NEXT GEN SAMPLE LIST",
            "0000",
            "0000"
        )
        custom_form.samples = samples

        smp_uris = LIMS_API.batch_post_samples(samples, prj)
        assert smp_uris is not None

        smp_art_uris = LIMS_API.tools.get_arts_from_samples(smp_uris)
        assert smp_art_uris is not None

        art_uris = [smp_art_uris[smp_uri] for smp_uri in smp_art_uris.keys()]
        assert art_uris is not None

        LIMS_UTIL.route_strategy(art_uris, custom_form, "dev")


def _post_researcher(current_time, res=None):
    """Method that will post a researcher and return a request."""

    if res is None:
        res = api_types.Researcher(
            f"Test-{current_time}",
            "Last Name",
            f"{LIMS_API.tools.api.host}labs/1",
            "TEST@email.arizona.edu",
            "")

    template_path = (os.path.join(
        os.path.split(__file__)[0], "post_researcher_template.xml"))
    with open(template_path, 'r') as file:
        template = Template(file.read())
        response_xml = template.render(
            first_name=res.first_name,
            last_name=res.last_name,
            lab_uri=res.lab_type,
            email=res.email)
    url = f"{LIMS_API.tools.api.host}researchers"
    return LIMS_API.tools.api.post(url, response_xml)


def _post_project(prj=None):
    """Method that will post a project and return an api_types.Project."""
    template_path = (os.path.join(
        os.path.split(__file__)[0], "post_project_template.xml"))
    with open(template_path, 'r') as file:
        template = Template(file.read())
        response_xml = template.render(
            name=f"Project_TEST_{datetime.now()}",
            open_date=str(datetime.today().date()),
            res_uri=f"{LIMS_API.tools.api.host}researchers/1")

    prj_response = LIMS_API.tools.api.post(
        f"{LIMS_API.tools.api.host}projects", response_xml)

    prj_response_soup = BeautifulSoup(
        prj_response, "xml").find("prj:project")
    prj = api_types.Project(
        prj_response_soup.find("name"),
        DEFAULT_RES,
        datetime.today().date(),
        [],
        prj_response_soup["uri"])

    return prj


def _post_con(name):
    """Method that will post a container and return a request."""
    template_path = (os.path.join(
        os.path.split(__file__)[0], "post_container_template.xml"))
    type_uri = f"{LIMS_API.tools.api.host}containertypes/1"
    with open(template_path, 'r') as file:
        template = Template(file.read())
        response_xml = template.render(con_name=name, type_uri=type_uri)

    return LIMS_API.tools.api.post(
        f"{LIMS_API.tools.api.host}containers",
        response_xml)


def _generate_samples(samples_data_table=None):
    """Method that will create  samples that can be posted."""
    samples_data_table = samples_data_table or dict()

    con_name = f"Auto_Sample_Test_{datetime.now()}"
    con_result_soup = BeautifulSoup(_post_con(con_name), "xml")
    con_uri = con_result_soup.find("con:container")["uri"]

    sample_list = list()
    for i in range(1, 97, 2):
        well = (
            'ABCDEFGH'[(i - 1) % 8] + ':' + '%01d' % ((i - 1) // 8 + 1,))
        letter = 'ABCDEFGH'[i % 8]
        to_add = api_types.Sample(f"test{i}{letter}")
        to_add.location = well
        to_add.con = api_types.Container(
            con_name,
            "96 well plate",
            "",
            con_uri)

        for data_name, data_value in samples_data_table.items():
            if "udf" in data_name:
                udf_name = data_name.strip("udf_")
                to_add.udf_to_value[udf_name] = data_value
            elif "adapter" in data_name:
                to_add.adapter = data_value
        sample_list.append(to_add)
    return sample_list
