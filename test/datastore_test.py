"""Exercise the functionality in the datastore management module."""
import random

from pudl.workspace import datastore as datastore


class TestDatastore:
    """Test the Datastore functions."""

    def test_doi_to_url(self, pudl_datastore_fixture):
        """Get the DOI url right."""
        number = random.randint(100000, 999999)  # nosec
        fake_doi = f"10.5072/zenodo.{number}"

        assert pudl_datastore_fixture.doi_to_url(fake_doi) == \
            f"https://sandbox.zenodo.org/api/deposit/depositions/{number}"

    def test_all_datapackage_json_available(self, pudl_datastore_fixture):
        """
        Ensure that every recorded DOI has a datapackage.json file.

        Integration test!
        """

        def test_it(client, doi):
            jsr = client.remote_datapackage_json(doi)

            assert "title" in jsr, f"No title for {doi}"
            assert "resources" in jsr, f"No resources for {doi}"
            assert jsr["profile"] == "data-package", \
                f"Incorrect profile for {doi}"

        # Yes, you could nest these too, but it's too clever for testing
        for _, doi in datastore.DOI["sandbox"].items():
            test_it(pudl_datastore_fixture, doi)

        # TODO:  When we have production data available, uncomment.
        # pudl_datastore_fixture.sandbox = False
        # for _, doi in datastore.DOI["production"].items():
        #     test_it(pudl_datastore_fixture, doi)
