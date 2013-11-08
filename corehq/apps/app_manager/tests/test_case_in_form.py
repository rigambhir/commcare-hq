import os

from django.test import TestCase

from corehq.apps.domain.shortcuts import create_domain
from corehq.apps.domain.models import Domain
from corehq.apps.app_manager.models import Application, APP_V1, APP_V2
from corehq.apps.app_manager.case_in_form import (get_references,
    RefType)


class CaseInFormTest(TestCase):
    domain = 'test-domain'

    parent_type = RefType.PARENT_CASE
    child_type = RefType.OWN_CASE

    # to ensure we're not getting incorrect results due to local state
    @property
    def this_app(self):
        return Application.get(self.this_app_id)

    @property
    def other_app1(self):
        return Application.get(self.other_app1_id)

    @property
    def other_app2(self):
        return Application.get(self.other_app2_id)

    def setUp(self):
        def read(filename):
            path = os.path.join(os.path.dirname(__file__), "data", filename)
            with open(path) as f:
                return f.read()

        create_domain(self.domain)

        this_app = Application.new_app(
                self.domain, "This App", application_version=APP_V2)

        parent_module = this_app.new_module("Parent Module", 'en')
        parent_module = this_app.get_module(0)
        parent_module.case_type = self.parent_type
        
        parent_form = this_app.new_form(
                parent_module.id, name="Create Parent", lang='en')
        parent_form.actions.open_case = {
            "condition": {
                "answer": None,
                "doc_type": "FormActionCondition",
                "question": None,
                "type": "always"
                },
            "doc_type": "OpenCaseAction",
            "external_id": None,
            "name_path": "/data/name"
        }
        parent_form.actions.update_case = {
            "condition": {
                "answer": None,
                "doc_type": "FormActionCondition",
                "question": None,
                "type": "always"
                },
            "doc_type": "UpdateCaseAction",
            "update": {
                "parent_property_1": "/data/parent_property_1"
            }
        }

        child_form = this_app.new_form(
                parent_module.id, name="Create Child", lang='en',
        child_form.actions.subcases = [
            {
                "case_name": "/data/child_name",
                "case_properties": {
                    "child_property_1": "/data/child_property_1"
                },
                "case_type": self.child_type,
                "condition": {
                    "answer": None,
                    "doc_type": "FormActionCondition",
                    "question": None,
                    "type": "always"
                },
                "doc_type": "OpenSubCaseAction",
                "reference_id": None,
            }
        ]

        child_module = this_app.new_module("Child Module", 'en')
        child_module = this_app.get_module(1)
        child_module.case_type = self.child_type
        update_child = this_app.
                attachment=read('case_in_form.xml'))
        #this_app.new_form(
                #parent_module.id, name="Update Parent and Create Child",
                #lang='en', attachment="")

        #child_module = this_app.new_module("Child Module", 'en')
        #child_module = this_app.get_module(1)
        #child_module.case_type = self.child_type
        #this_app.new_form(
                #child_module.id, name="Edit Child", lang='en', attachment=\
                #""" """)

        this_app.save()
        self.this_app_id = this_app._id

        #other_app1 = Application.new_app(
                #self.domain, "Other App (Child)", 
                #application_version=APP_V2)
        #self.other_app1_id = other_app1._id
        #other_module = other_app1.new_module("Other Module (Child)", 'en')
        #other_module = other_app1.get_module(0)
        #other_module.case_type = self.child_type
        #other_app1.new_form(
                #other_module.id, name="Edit Child (Other App)", lang='en', attachment=\
                #""" """)

        #other_app1.save()
        #self.other_app1_id = other_app1._id

        #other_app2 = Application.new_app(
                #self.domain, "Other App (Parent)", 
                #application_version=APP_V2)
        #other_module = other_app2.new_module("Other Module (Parent)", 'en')
        #other_module = other_app2.get_module(0)
        #other_module.case_type = self.parent_type
        #other_app2.new_form(
                #other_module.id, name="Edit Parent (Other App)", lang='en', attachment=\
                #""" """)

        #other_app2.save()
        #self.other_app2_id = other_app2._id


    def tearDown(self):
        self.this_app.delete()
        #self.other_app1.delete()
        #self.other_app2.delete()

    def test_get_case_properties(self):
        self.assertEqual(get_case_properties(Domain.get_by_name(self.domain)), {
            self.parent_type: {
                "name": [
                ],
                "parent_property_1": [
                ]
            },
            self.child_type: {
                "name": [
                ],
                "child_property_1": [
                ]
            }
        })

    def test_get_all_references_for_form(self):
        form = self.this_app.get_module(1).get_form(0)

        expected_references = sorted([
            {
                'question': '/data/question1',
                'case_type': self.child_type,
                'property': 'child_property_1',
                'type': RefType.CONSTRAINT
            },
            {
                'question': '/data/question1',
                'case_type': self.parent_type,
                'property': 'parent_property_1',
                'type': RefType.RELEVANT
            },
            {
                'question': '/data/question1',
                'case_type': self.child_type,
                'property': 'nonexistent_child_property',
                'type': RefType.LABEL_ITEXT,
            },
            {
                'question': '/data/question1',
                'case_type': self.child_type,
                'property': 'child_property_1',
                'type': RefType.LABEL_ITEXT,
            },
            {
                'question': '/data/question1',
                'case_type': self.parent_type,
                'property': 'parent_property_1',
                'type': RefType.HINT_ITEXT,
            },
            {
                'question': '/data/question1',
                'case_type': self.parent_type,
                'property': 'parent_property_1',
                'type': RefType.CONSTRAINT_ITEXT,
            },
            {
                'question': '/data/question2',
                'case_type': self.child_type,
                'property': 'nonexistent_child_property',
                'type': RefType.LABEL_ITEXT,
            },
            {
                'question': '/data/question3',
                'case_type': self.child_type,
                'property': 'child_property_1',
                'type': RefType.SETVALUE,
            },
        ])

        def coalesce(references):
            foo = {}
            for r in references:
                if r['question'] not in foo:
                    foo[r['question']] = []
                foo[r['question']].append(r)
            return foo

        references = sorted(get_references(form))
        import pprint
        pprint.pprint(coalesce(references))
        pprint.pprint(coalesce(expected_references))
        # we don't care about order
        self.assertEqual(references, expected_references)

    #def test_check_validity_of_reference(self):
        #xform = self.this_app.modules[1].forms[0]

        #references = get_references(xform, validate=True)
        #bad_references = [r for r in references 
                #if r['property'] == 'nonexistent_child_property']

        #self.assertTrue(bad_references)
        #self.assertTrue(all(r['valid'] == False for r in bad_references))

    #def test_get_relevant_references_in_project(self):
        #pass

    #def test_rename_reference_in_itext(self):
        #pass
    
    #def test_rename_reference_in_logic_for_all_langs(self):
        #pass

    #def test_rename_two_copies_of_reference_in_logic_condition(self):
        #pass

    #def test_rename_all_references_explicitly(self):
        #pass

    ## implicit tests using rename: True in update_references()
    #def test_rename_all_references_implicitly(self):
        ## rename a parent property.  It should get renamed 
        ##   in {references, updates, setvalues} 
        ##   in {create parent, update parent, edit child, edit (parent app),
        ##     edit (child app)}
        ## rename a child property. It should get renamed
        ##   in {references, updates, setvalues} in the edit child and edit
        ##   (child app) forms
        ##   in updates in the update parent/create child form

        ## rename a parent property using an explicit exclude_form.  None of
        ## the references in that form should be renamed.
        #pass

    #def test_rename_all_references_implicity_excluding_source_form(self):
        #pass

    #def test_rename_some_references_explicitly(self):
        #pass
