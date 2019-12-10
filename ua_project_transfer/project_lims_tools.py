"""Contains tools required to submit projects to Clarity."""
import os
import logging
import logging.config
import traceback
import datetime
from bs4 import BeautifulSoup
from jinja2 import Template
from ua_clarity_tools import ua_clarity_tools
from ua_project_transfer import core_specifics


LOGGER = logging.getLogger(f"__main__.{__name__}")


class POSTNameCollision(Exception):
    """You tried to POST something with a name that is already in Clarity."""


class POSTException(Exception):
    """The POST failed."""


class ProjectLimsApi:
    """The class that holds the initialized clarity_tools."""

    def __init__(self, host, username, password):
        self.tools = ua_clarity_tools.ClarityTools(host, username, password)

    def get_researcher_uri(self, res):
        """Get the uri's of all researchers in Clarity with the given name.

        Arguments:
            res (dataclass):
                A dataclass called Researcher defined in api_types, with the
                fields: "first_name", "last_name", "lab_type", "email", and
                "uri", where all of these are strings and lab_type is either
                'internal' or 'external'.

        Returns:
            res_uris (list of strings):
                A list that of all the uris with names
                that match the given res.first_name and res.last_name, case
                insensitive.

        Notes:
            The onus of responsibility for checking the size of this list is
                on the caller.
        """
        parameters = {"firstname": res.first_name, "lastname": res.last_name}
        res_soup = BeautifulSoup(self.tools.api.get(
            "researchers", parameters=parameters), "xml")

        res_uris = list()
        for researcher in res_soup.find_all("researcher"):
            res_uris.append(researcher["uri"])

        return res_uris

    def post_researcher(self, res):
        """Add a new researcher to Clarity.

        Arguments:
            res (dataclass):
                A dataclass called Researcher defined in api_types, with the
                fields: "first_name", "last_name", "lab_type", "email", and
                "uri", where all of these are strings and lab_type is either
                'internal' or 'external'.

        Returns:
            (string):
                The uri of the newly posted researcher.

        Side Effects:
            If successful, this function will post the researcher to the
                Clarity REST DB.

        Raises:
            POSTNameCollision
            POSTException
        """
        # Check for collision.
        current_uri = self.get_researcher_uri(res)
        if current_uri != []:
            raise POSTNameCollision(
                "There is already a researcher with that name. Choose a"
                " different one and try again.")

        # Hardcoded for the default Administrative Lab.
        lab_uri = f"{self.tools.api.host}labs/1"

        # Build and submit the xml request. Pass in the directory that this
        # module is in, by finding the folder relative to the __file__
        # attribute of this module.
        research_template_path = os.path.join(
            os.path.split(__file__)[0],
            "post_researcher_template.xml")

        with open(research_template_path, 'r') as file:
            template = Template(file.read())
            res_xml = template.render(
                first_name=res.first_name,
                last_name=res.last_name,
                lab_uri=lab_uri,
                email=res.email)

        res_post = self.tools.api.post("researchers", res_xml)

        res_post_soup = BeautifulSoup(res_post, "xml")
        new_researcher_uri = res_post_soup.find("res:researcher")["uri"]

        return new_researcher_uri

    def post_project(self, prj_info):
        """Add a new project to Clarity.
        Arguments:
            prj_info (dataclass):
                A dataclass called Project, defined in api_types, with the
                fields: "name", "res", "open_date", "files", "uri", where all
                of these are strings.

        Returns:
            (string):
                The uri of the posted project.

        Side Effects:
            If successful, this function will post the project to the
                Clarity REST DB.

        Raises:
            POSTNameCollision
            POSTException
        """
        # Get will return xml, but only have the project tag if a project was
        # found.
        prjs_soup = BeautifulSoup(self.tools.api.get(
            "projects", parameters={"name": prj_info.name}), "xml")
        if prjs_soup.find("project"):
            raise(POSTNameCollision(
                "There is already a project with that name. Choose a"
                " different one and try again."))

        # Build and submit the xml request.
        project_template_path = os.path.join(
            os.path.split(__file__)[0],
            "post_project_template.xml")

        with open(project_template_path, 'r') as file:
            template = Template(file.read())
            project_xml = template.render(
                name=prj_info.name,
                open_date=prj_info.open_date,
                researcher_uri=prj_info.res.uri)

        prj_post = self.tools.api.post("projects", project_xml)

        prj_post_soup = BeautifulSoup(prj_post, "xml")
        new_project_uri = prj_post_soup.find("prj:project")["uri"]
        return new_project_uri

    def batch_post_containers(self, samples, prj_name):
        """Add new containers to Clarity.

        Arguments:
            samples (list of samples): The samples that contain a
                fully-formed Container in their .con value, where fully-formed
                here means having a con.name and con.con_type.
            prj_name (string): The name of the project where the samples in
                these containers are going to be posted.

        Returns:
            list_art_uris (list of  strings): The uri's of the containers that
                were just created.

        Side Effects:
            If successful, this function will post all of the containers in
                to the Clarity REST DB.

        Raises:
            POSTException
        """
        parameters = {"name": {sample.con.name for sample in samples}}
        exist_con_soup = BeautifulSoup(self.tools.api.get(
            "containers", parameters=parameters), "xml")
        found_cons = [con.name for con in exist_con_soup.find_all("container")]

        container_types_soup = BeautifulSoup(
            self.tools.api.get("containertypes"), "xml")
        contypes_uris = dict()
        for con_type in container_types_soup.find_all("container-type"):
            contypes_uris[con_type["name"]] = con_type["uri"]

        # Renaming container name if container name exists.
        con_post_collisions = set()
        for sample in samples:
            if sample.con.name in found_cons:
                con_post_collisions.add(sample.con.name)
                sample.con.name = f"{sample.con.name}-{prj_name}"

            # Check that the container type has been implemented.
            if sample.con.con_type in contypes_uris.keys():
                sample.con.con_type_uri = contypes_uris[sample.con.con_type]
            else:
                raise NotImplementedError(
                    f"The container type '{sample.con.con_type}' does not"
                    f" exist in this Clarity environment.")

        # Warn of any collisions.
        if con_post_collisions:
            LOGGER.warning({
                "template": os.path.join("general", "warning.html"),
                "content": (
                    f"The containers: {con_post_collisions} have the same name"
                    f" as another container in Clarity. These containers have"
                    f" been added to Clarity with their prj_names appended to"
                    f" their names.")
            })

        # Constructing various paths for use.
        con_template_path = os.path.join(
            os.path.split(__file__)[0], "post_containers_template.xml")
        batch_con_template_path = os.path.join(
            os.path.split(__file__)[0], "post_containers_batch_template.xml")

        # Constructing the xml objects for each artifact.
        con_xmls = list()
        con_infos = {
            (sample.con.name, sample.con.con_type_uri) for sample in samples}
        for name, uri in con_infos:
            with open(con_template_path, 'r') as file:
                template = Template(file.read())
                con_xml = template.render(con_name=name, con_type_uri=uri)
            con_xmls.append(con_xml)

        # Build the list that will be rendered by the Jinja template.
        with open(batch_con_template_path, 'r') as file:
            template = Template(file.read())
            container_xml = template.render(con_list='\n'.join(con_xmls))

        # Attempt to post.
        con_post = self.tools.api.post(
            "containers/batch/create", container_xml)

        # Get return info out of post.
        con_post_soup = BeautifulSoup(con_post, "xml")
        new_container_uris = [
            link["uri"] for link in con_post_soup.find_all("link")]

        # Check that the uris are gettable.
        BeautifulSoup(self.tools.api.get(new_container_uris), "xml")

        return new_container_uris

    def batch_post_samples(self, samples, prj_info):
        """Add samples to a project in Clarity.

        Arguments:
            samples (list of samples):
                Sample is a class defined in data_types. These objects must
                have the requisite info to post a sample: a container_uri,
                location, name, and a udf name: udf value dictionary.
            prj_info (dataclass):
                A dataclass called Project,  with the fields: "name", "res",
                "open_date", "files", "uri", where all of these are strings.

        Returns:
            (list of strings):
                The uri's of the samples that were just created.

        Side Effects:
            If successful, this function will post all of the samples in
                samples to the Clarity REST DB.

        Raises:
            requests.exceptions.HTTPError
        """

        sample_template_path = os.path.join(
            os.path.split(__file__)[0], "post_samples_template.xml")
        batch_sample_template_path = os.path.join(
            os.path.split(__file__)[0], "post_samples_batch_template.xml")
        sample_xmls = list()

        # Construct each of the sample xml objects.
        for sample in samples:
            with open(sample_template_path, 'r') as file:
                template = Template(file.read())
                smp_xml = template.render(
                    name=sample.name,
                    prj_limsid=prj_info.uri.split('/')[-1],
                    prj_uri=prj_info.uri,
                    con_uri=sample.con.uri,
                    location=sample.location,
                    udf_dict=sample.udf_to_value)
            smp_xml = smp_xml.replace('&', "&amp;")
            sample_xmls.append(smp_xml)

        # Compile all of the sample xmls into a batch sample xml object.
        with open(batch_sample_template_path, 'r') as file:
            template = Template(file.read())
            batch_xml = template.render(
                samples='\n'.join(sample_xmls))

        # If the sample has a UDF that is unknown to Clarity, remove it from
        # the xml for all samples, and try to post again.
            valid_udfs = self.tools.get_udfs("Sample")
            batch_soup = BeautifulSoup(batch_xml, "xml")
            for udf_tag in batch_soup.find_all("udf:field"):
                if udf_tag["name"] not in valid_udfs:
                    udf_tag.decompose()

        response = self.tools.api.post("samples/batch/create", batch_soup)
        samples_post_soup = BeautifulSoup(response, "xml")

        sample_uris = [x["uri"] for x in samples_post_soup.find_all("link")]

        # Add adapter info to sample's artifacts in Clarity if provided.
        if [sample.adapter for sample in samples if sample.adapter]:
            # Map created artifacts to samples, as I am not comfortable relying
            # on the sample_uri links being in the same order as samples.
            smp_art_uris = self.tools.get_arts_from_samples(sample_uris)
            arts_soup = BeautifulSoup(
                self.tools.api.get(list(smp_art_uris.values())), "xml")

            art_limsid_label = dict()
            for art in arts_soup.find_all("art:artifact"):
                for sample in samples:
                    # If location and con_uri are ==, they map to each other.
                    if (art.find("container")["uri"] == sample.con.uri
                            and art.find("value").text == sample.location):
                        art_limsid_label[art["limsid"]] = sample.adapter
            self.tools.set_reagent_label(art_limsid_label)

        return sample_uris


class LimsUtility():
    """Contains project_transfer-specific wrappers for project_lims_api."""
    def __init__(self, host, username, password):
        self.lims_api = ProjectLimsApi(host, username, password)

    def create_researcher(self, req_id, prj_info):
        """Create researcher from info in the passed-in prj_info object.

        Arguments:
            req_id (string):
                The request's ID value.
            prj_info (dataclass):
                The Project_Info object with a researcher containing a first
                and last name.

        Returns:
            prj_info.res.uri(string):
                The uri of the researcher just posted or found.

        Side Effects:
            - The prj_info.res.uri is set to the uri that was posted or found.
        """
        try:
            res_uri = self.lims_api.post_researcher(prj_info.res)

        except POSTNameCollision:
            prj_info.res.uri = self.lims_api.get_researcher_uri(
                prj_info.res)[0]
            return prj_info.res.uri

        # Continuation of try, do it this way if the researcher was newly
        # posted in the try block without errors.
        else:
            prj_info.res.uri = res_uri

        return prj_info.res.uri

    def create_project(self, req_id, prj_info):
        """Create project from info in the passed-in prj_info object.

        Arguments:
            req_id (string):
                The request's ID value.
            prj_info (dataclass):
                The Project_Info object with a well-formed researcher.

        Returns:
            prj_info.uri(string):
                The uri of the project that was just posted.

        Side Effects:
            Sets the passed-in prj_info's open_date to today, and uri to the
                one just posted.
        """

        prj_info.open_date = datetime.date.today().__str__()
        prj_uri = self.lims_api.post_project(prj_info)

        prj_info.uri = prj_uri
        return prj_info.uri

    def create_containers(self, req_id, prj_info, current_form):
        """Creates containers from info in the passed-in current_form object.

        Arguments:
            req_id (string):
                The request's ID value.
            prj_info (dataclass):
                The Project_Info object with a well-formed researcher.
            current_form (dataclass):
                The Custom_Form object with well-formed samples.

        Returns:
            con_uris (list):
                The uris of the containers that were just posted.

        Side Effects:
            Sets the samples' con_uris if it succeeds.
        """
        try:
            con_uris = self.lims_api.batch_post_containers(
                current_form.samples, prj_info.name)

        except POSTException:
            raise

        else:
            con_soups = BeautifulSoup(
                self.lims_api.tools.api.get(con_uris), "xml")
            con_names_uris = dict()
            for soup in con_soups.find_all("con:container"):
                con_name = soup.find("name").text
                con_uri = soup["uri"]
                con_names_uris[con_name] = con_uri
            for sample in current_form.samples:
                # Find what the name of the posted container was.
                posted_con_uri = con_names_uris.get(sample.con.name)
                if posted_con_uri is None:
                    dup_con_name = sample.con.name + '-' + prj_info.name
                    posted_con_uri = con_names_uris.get(dup_con_name)
                sample.con.uri = posted_con_uri

            return con_uris

    def create_samples(self, req_id, prj_info, current_form):
        """Creates samples from info in the passed-in current_form object.

        Arguments:
            req_id (string):
                The request's ID value.
            prj_info (dataclass):
                The Project_Info object with a well-formed researcher.
            current_form (dataclass):
                The Custom_Form object with well-formed samples.

        Returns:
            sample_uris (list):
                The uris of the containers that were just posted.

        Side Effects:
            Sets the samples' uri's and artifact uri's if it succeeds.
        """
        sample_uris = self.lims_api.batch_post_samples(
            current_form.samples, prj_info)

        submitted_sample_soup = BeautifulSoup(
            self.lims_api.tools.api.get(sample_uris), "xml")
        for smp_soup in submitted_sample_soup.find_all("smp:sample"):
            for sample in current_form.samples:
                if sample.name == smp_soup.find("name").text:
                    sample.uri = smp_soup["uri"]

        sample_art_uris = self.lims_api.tools.get_arts_from_samples(
            sample_uris)
        for sample in current_form.samples:
            sample.art_uri = sample_art_uris[sample.uri]

        return sample_uris

    def route_strategy(self, artifact_uris, form, env):
        """Implements strategy pattern to determine how to route samples.

        Arguments:
            artifact_uris (list of strings):
                The uri's to route.
            form (CustomForm):
                The CustomForm associated with a service request.
            env (string):
                The key that maps to the desired set of workflows and steps in
                wf_steps.WF_STEPS.

        Side Effects:
            Routes samples in Clarity if successful."""
        # A dictionary that maps the form name to the appropriate function.
        route_strategy_payload = {
            "lims_api": self.lims_api,
            "art_uris": artifact_uris,
            "form": form,
            "env": env}

        # NOTE: Additionally, skip any forms with "REQUEST A QUOTE" in the form
        # names, case insensitive.
        if (form.name.strip().upper() in core_specifics.UNROUTABLE_FORMS
                or "REQUEST A QUOTE" in form.name.strip().upper()):
            return
        route_function = core_specifics.WF_LOCATIONS.get(form.name)

        if route_function:
            route_function(route_strategy_payload)
        # If the form was not skipped and has not been mapped, email an error.
        else:
            req_type = form.request_type
            LOGGER.warning({
                "template": os.path.join(
                    "project_transfer", "route_warning.html"),
                "content": (
                    f"The request type {req_type} with the form {form.name}"
                    f" has not yet been implemented. The samples in req:"
                    f" {form.req_id} have not been routed. The exception that"
                    f" was thrown is {traceback.format_exc()}")
            })
