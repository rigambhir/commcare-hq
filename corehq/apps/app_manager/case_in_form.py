"""
This module contains code relating to parsing and updating instance('casedb')
case property references in forms.

In order to make the instance('casedb') workflow work, we need to be able to
rename property references in other forms when a saved property gets renamed
while editing one form. These references could be in a child case form or a
case sharing form or any other form that is able to load properties from any of
the case types that the one form has the ability to save to.

The references can be
- loading using a <setvalue/>
- references in a logic condition or itext message
- saving to a property (of parent, child, or own case) with the same name in a
  case update

We need to know whether to update each of these references. This requires
passing Vellum a list of all relevant references on load so it can let the user
change the default (rename) to not rename (possibly granularly with respect to
all the different references) whenever they rename a saved property that is
referenced somewhere else in the project.  Then, we need to be able to change
all of these references based on the data Vellum passes back on save about what
the user decided to do.

Edge case: references in normalized itext questions.

For now we do not allow the user to differentiate between different rename
actions for different types of references (setvalue, reference, save) for a
single question.

An edge case is if a second form is edited at the same time to add a case
property reference that the first editing session will no longer know
about.  For now we will just ignore the issue of renaming those references
and let them show up as invalid references the next time that form is
loaded (rather than, say, display a list of new references in the second
form when the user attempts to save the first form and make them choose
what to do for each of the references).

We are requiring the client to pass a full explicit definition of
references to remain rather than allow them to rename all the references
for a property globally or for a form in order to prevent having to first
look up the references and group them (which wouldn't really be too hard),
but also to ensure that any client knows that it has to be explicit.


Renaming not handled/undefined behavior for:
- when two modules create child cases in one module
- when a form creates multiple child cases with different case types
"""

import re
from collections import defaultdict
from xml.etree import ElementTree

from django.utils.translation import ugettext_noop, ugettext as _

#from corehq.apps.app_manager.models import Application
from corehq.apps.app_manager.xform import XFormError
from corehq.apps.app_manager.util import (get_all_case_properties,
        ParentCasePropertyBuilder)


__all__ = ['get_references', 'get_validated_references', 'get_reftype_names'
    #'RefType', 'ModuleType'
]

# these are duplicated in formdesigner.commcare.js
PROPERTY_NAME = r"([a-zA-Z][\w_-]*)"
CASE_PROPERTY_PREFIX = r"instance('casedb')/casedb/case[@case_id=instance('commcaresession')/session/data/case_id]/"
# hack. (?!\=\s*) is a negative lookahead as a safeguard against matching
# references within other references (although we guard against that in the
# replacing too).
CASE_PROPERTY = re.compile(
    r"(?!\=\s*)" + re.escape(CASE_PROPERTY_PREFIX) + PROPERTY_NAME)

PARENT_CASE_PROPERTY_PREFIX = r"instance('casedb')/casedb/case[@case_id=instance('casedb')/casedb/case[@case_id=instance('commcaresession')/session/data/case_id]/index/parent]/"
PARENT_CASE_PROPERTY = re.compile(
    r"(?!\=\s*)" + re.escape(PARENT_CASE_PROPERTY_PREFIX) + PROPERTY_NAME)


# constants for reference types
# we don't handle non-itext messages
class RefType(object):
    # TODO: calculate condition on bind!

    SETVALUE = 'setvalue'
    RELEVANT = 'relevant'
    CONSTRAINT = 'constraint'
    LABEL_ITEXT = 'label_itext'
    CONSTRAINT_ITEXT = 'constraint_itext'
    HINT_ITEXT = 'hint_itext'
    #SAVE_TO_OWN_CASE = 'save_to_own_case'
    #SAVE_TO_PARENT_CASE = 'save_to_parent_case'
    #SAVE_TO_CHILD_CASE = 'save_to_child_case'

    OWN_CASE = 'own_case'
    PARENT_CASE = 'parent_case'
    # for subcase creation save to case references
    #CHILD_CASE = 'child_case'

REFTYPE_NAMES = {
    RefType.SETVALUE: ugettext_noop('Load Value'),
    RefType.RELEVANT: ugettext_noop('Display Condition'),
    RefType.CONSTRAINT: ugettext_noop('Validation Condition'),
    RefType.LABEL_ITEXT: ugettext_noop('Label'),
    RefType.CONSTRAINT_ITEXT: ugettext_noop('Validation Message'),
    RefType.HINT_ITEXT: ugettext_noop('Hint Message')
}

def get_reftype_names():
    """Get translated names for attributes that can reference a case
    property"""
    return dict([(k, _(v)) for (k, v) in REFTYPE_NAMES.items()])

#class ModuleType(object):
    #PARENT = 'parent_module'   # may not necessarily actually have any child forms
    #CHILD = 'child_module'


#def get_relevant_references(project, form=None, validate=True):
    #"""
    #Returns a list of relevant case property references for each form in this
    #project that has a case type or a parent case type which can be saved to by
    #`form`.

    #If `form` is None, return all references in the project.
    #"""
    #app_structure = get_relevant_app_structure(project, form)
    #for app in app_structure:
        #for module in app['modules']:
            #for form in module['forms']:
                #form['references'] = [
                    #r for r in get_references(form['form'])
                    #if (
                        #(module['module_type'] == ModuleType.CHILD and
                        #r['case_type'] == RefType.PARENT_CASE) or
                        #(module['module_type'] == ModuleType.PARENT and
                        #r['case_type'] == RefType.OWN_CASE)
                    #)
                #]
    #return app_structure


#def get_case_properties(project):
    #apps = Application.by_domain(project.name)

    ## dict per case type, of property name -> list of source questions
    #properties = defaultdict(lambda: defaultdict(list))

    ## first we need to figure out the parent case type.
    ## One case type could be created from multiple parent case types but for
    ## now we aren't going to do anything with that information.
    ##parent_case_types = []
    ##for app in apps:
        ##for module in app.get_modules():
            ##for form in module.get_forms():
                ##if any(s.case_type == own_case_type for s in
                        ##form.actions.subcases):
                    ##parent_case_types.append(module.case_type)

    #def process_form(form):
        #module = form.get_module()
        #form_case_type = module.case_type
        #questions_by_path = defaultdict(lambda: None, (
            #(q['value'], dict(form_id=form.id, module_id=module.id, **q))
            #for q in form.questions))
        #open_case = form.actions.open_case
        #update_case = form.actions.update_case

        #if open_case.condition.type != 'never' and open_case.name_path:
            #properties[form_case_type]['name'].append(
                    #questions_by_path[open_case.name_path])

        #if update_case.condition.type != 'never':
            #for property, path in update_case.update.items():
                #properties[form_case_type][property].append(
                        #questions_by_path[path])

        #for subcase in form.actions.subcases:
            #properties[subcase.case_type]['name'].append(
                    #questions_by_path[subcase.case_name])
            #for property, path in subcase.case_properties.items():
                #properties[subcase.case_type][property].append(
                        #questions_by_path[path])

    ## user registration forms?
    #for app in apps:
        #for module in app.get_modules():
            #for form in module.get_forms():
                #process_form(form)
    #return properties

def get_references(form):
    """
    Get all case property references in `xform`
    [
        {
            'question': '/data/question1',
            'case_type': RefType.OWN_CASE|RefType.PARENT_CASE,
            'property': 'foo',
            'type': RefType.FOO,
        }
    ]
    Multiple actual references of a given type return only one entry (i.e.,
    multiple references in the same condition, or multiple references in the
    same itext message in different languages).
    """
    all_references = defaultdict(list)
    def collect_parsed_references(property_value):
        value = property_value['value']
        question = property_value.pop('question')
        for r in parse_references(value):
            # for now we don't care about multiple references to the same property in
            # the same question and attribute
            ref = dict(r, **property_value)
            if all(ref != x for x in all_references[question]):
                all_references[question].append(ref)
        return value
    for_each_property_value(form.wrapped_xform(), collect_parsed_references)

    return all_references # + get_save_to_case_references(form)

def get_validated_references(form):
    references = get_references(form)

    case_type = form.get_module().case_type
    case_properties = get_all_case_properties(form.get_app())[case_type]

    for question, refs in references.items():
        for r in refs:
            if r['case_type'] == RefType.OWN_CASE:
                property = r['property']
            else:  # PARENT_CASE
                property = 'parent/%s' % r['property']
            r['valid'] = property in case_properties

    return references

#def get_save_to_case_references(form):
    #references = []
    #open_case = form.actions.open_case
    #update_case = form.actions.update_case

    #if open_case.condition !== 'never' and open_case.name_path:
        #references.append({
            #'property': 'name'
            #'question': open_case.name_path,
            #'case_type': RefType.OWN_CASE,
            #'type': RefType.SAVE_TO_OWN_CASE
        #})
    #if update_case.condition !== 'never':
        #for prop_name, path in update_case.update.items():
            #if prop_name.startswith('parent/'):
                #type = RefType.SAVE_TO_PARENT_CASE
                #case_type = RefType.PARENT_CASE
            #else:
                #type = RefType.SAVE_TO_OWN_CASE
                #case_type = RefType.OWN_CASE
            #references.append({
                #'property': prop_name,
                #'question': path,
                #'case_type': case_type,
                #'type': type
            #})
    #for subcase in form.actions.subcases:
        #references.append({
            #'property': 'name',
            #'question': subcase.case_name,
            #'case_type': RefType.CHILD_CASE,
            #'type': RefType.SAVE_TO_CHILD_CASE
        #})
        #for prop_name, path in subcase.case_properties.items():
            #references.append({
                #'property': prop_name,
                #'question': path,
                #'case_type': RefType.CHILD_CASE,
                #'type': RefType.SAVE_TO_CHILD_CASE
            #})
    #return references


def overlapping(start, end, ranges):
    return any(
        (start >= s and start < e) or
        (end > s and end <= e)
        for (s, e) in ranges
    )


def parse_references(value_string):
    # don't parse case property references within parent property references
    parent_ranges = []
    # avoid more than one reference entry per property name per case type
    parent_references = {}
    case_references = {}
    for match in re.finditer(PARENT_CASE_PROPERTY, value_string):
        parent_ranges.append((match.start(), match.end()))
        property = match.group(1)
        parent_references[property] = {
            'case_type': RefType.PARENT_CASE,
            'property': property
        }

    for match in re.finditer(CASE_PROPERTY, value_string):
        if not overlapping(match.start(), match.end(), parent_ranges):
            property = match.group(1)
            case_references[property] = {
                'case_type': RefType.OWN_CASE,
                'property': property
            }

    return ([r for (k, r) in parent_references.items()] +
            [r for (k, r) in case_references.items()])


def get_path(node, xform):
    try:
        return xform.get_path(node)
    except XFormError:
        return False


def for_each_property_value(xform, callback):
    head = xform.find('{h}head')
    model = head.find('{f}model')

    # head: setvalues
    for setvalue in head.findall('{f}setvalue'):
        question = get_path(setvalue, xform)
        value = setvalue.attrib.get('value')
        if question and value:
            setvalue.attrib['value'] = callback({
                'question': question,
                'value': value,
                'type': RefType.SETVALUE
            })

    # bind: relevant, constraint, and constraint itext
    for bind in model.findall('{f}bind'):
        question = get_path(bind, xform)
        if not question:
            continue
        relevant = bind.attrib.get('relevant')
        constraint = bind.attrib.get('constraint')
        if relevant:
            bind.attrib['relevant'] = callback({
                'question': question,
                'value': relevant,
                'type': RefType.RELEVANT
            })
        if constraint:
            bind.attrib['constraint'] = callback({
                'question': question,
                'value': constraint,
                'type': RefType.CONSTRAINT
            })

        constraintMsgID = bind.attrib.get('{jr}constraintMsg')
        if constraintMsgID:
            for_each_itext_value(xform, constraintMsgID,
                    lambda v: callback({
                        'question': question,
                        'value': value,
                        'type': RefType.CONSTRAINT_ITEXT
                    }))

    # control: label and hint itext
    def control_node_fn(node, path, repeat_context, items):
        def node_to_refs(node, type):
            message_nodes = filter(None,
                [i.find(type) for i in items or []] +
                [node.find(type)]
            )
            return filter(None, [n.attrib.get('ref') for n in message_nodes])
        for itext_ref in node_to_refs(node, '{f}label'):
            for_each_itext_value(xform, itext_ref,
                    lambda v: callback({
                        'question': path,
                        'value': v,
                        'type': RefType.LABEL_ITEXT
                    }))
        for itext_ref in node_to_refs(node, '{f}hint'):
            for_each_itext_value(xform, itext_ref,
                    lambda v: callback({
                        'question': path,
                        'value': v,
                        'type': RefType.HINT_ITEXT
                    }))

    xform.for_each_leaf_control_node(control_node_fn)


def for_each_itext_value(xform, itext_ref, callback):
    # jr:itext('foo') -> foo
    try:
        itext_id = itext_ref[10:-2]
    except IndexError:
        return

    items = xform.model_node.findall(
            '{f}itext/{f}translation/{f}text[@id="%s"]' % itext_id)
    for item in items:
        for i, value in enumerate(item.findall('{f}value')):
            # unwrap and stringify
            callback(ElementTree.tostring(value.xml))

            #item.remove(value)
            #item.insert(i, ElementTree.fromstring(
                #callback(ElementTree.tostring(value))))


#def update_references(project, properties, exclude_form=None):
    #"""
    #Update all property references specified in `properties` (including the
    #names of saved case properties).

    #`properties` is a list of properties to rename formatted like
    #[
        #{
            #'case_type': 'bar',
            #'old_name': 'foo',
            #'new_name': 'new_foo',
            #'rename': [
                #{
                    #'app_id': 'foobar',
                    #'module_id': 0,
                    #'form_id': 1,
                    #'questions': [
                        #'/data/question1',
                        #'/data/question2/question3',
                    #],
                    #'save_to_own_case': True,
                    #'save_to_parent_case': False,
                    #'save_to_child_case': False,
                #}
            #]
        #}
    #]
    #"""
    #app_structure = get_relevant_app_structure(project, exclude_form)
    #for app in app_structure:
        #for module in app['modules']:
            #for form in module['forms']:
                #form_relevant_properties = []
                #for p in properties:
                    #for r in p['rename']:
                        #if (r['app_id'] == app._id and 
                            #r['module_id'] == module['module'].id and 
                            #r['form_id'] == form['form'].id):
                            #form_relevant_properties.push(dict(r,
                                #case_type=module['module_type']))
                            #continue

                #if form_relevant_properties:
                    #update_form_references(form['form'], form_relevant_properties)


#def update_form_references(form, properties):
    #xform = form['form'].wrapped_xform()
    #grouped = {}
    #for p in properties:
        #if p['case_type'] not in grouped:
            #grouped[p['case_type']] = {}
        #grouped[p['case_type']][p['old_name']] = p

    #for case_type, rename_mapping in grouped.items():
        #def update_references(property_value):
            #if property_value['question'] in ren
            #return rename_references(property_value, case_type, rename_mapping)
        #for_each_property_value(xform, update_references)


#def update_save_to_case_references(form, properties):
    #pass


#def rename_references(property_value, case_type, rename_mapping):
    #orig_value = property_value['value'] 
    
    #replaced_ranges = []
    #def repl(replacement_prefix, match):
        #old_ref = match.group(0)
        #start = match.start()
        #end = match.end()
        #if overlapping(start, end, replaced_ranges):
            #return old_ref
        #old_name = match.group(1)
        
        #replaced_ranges.append((start, end))
        #if old_name in rename_mapping.get(case_type, []):
            #new_name = rename_mapping[match.group(1)]
            #return replacement_prefix + new_name
        #else:
            #return old_ref

    #regexes = {
        #ref.PARENT_CASE: PARENT_CASE_PROPERTY,
        #ref.CASE: CASE_PROPERTY
    #}
    #prefixes = {
        #ref.PARENT_CASE: PARENT_CASE_PROPERTY_PREFIX,
        #ref.CASE: CASE_PROPERTY_PREFIX
    #}
    #return re.sub(
            #regexes[case_type], partial(repl, prefixes[case_type]),
            #orig_value)
