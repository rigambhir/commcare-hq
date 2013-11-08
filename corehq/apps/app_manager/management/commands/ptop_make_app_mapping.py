from datetime import datetime
import pprint
from django.core.management.base import NoArgsCommand
import sys
import os
from corehq.apps.app_manager.models import Application
from corehq.apps.hqcase.management.commands.ptop_generate_mapping import MappingOutputCommand
from corehq.pillows import dynamic
from corehq.pillows.application import AppPillow
from corehq.pillows.dynamic import DEFAULT_MAPPING_WRAPPER, app_special_types
from django.conf import settings

class Command(MappingOutputCommand):
    help="Generate mapping JSON of our ES indexed types. For applications"
    option_list = NoArgsCommand.option_list + (
    )
    doc_class_str = "corehq.apps.app_manager.models.Application"
    doc_class = Application


    def finish_handle(self):

        filepath = os.path.join(settings.FILEPATH, 'corehq','pillows','mappings','app_mapping.py')
        app_pillow = AppPillow(create_index=False)

        #current index
        #check current index
        aliased_indices = app_pillow.check_alias()

        current_index = app_pillow.es_index

        #regenerate the mapping dict
        m = DEFAULT_MAPPING_WRAPPER

        init_dict = {
            "cp_is_active": {"type": "boolean"},
        }

        m['properties'] = dynamic.set_properties(self.doc_class, custom_types=app_special_types, init_dict=init_dict)
        m['_meta']['comment'] = "Autogenerated [%s] mapping from ptop_generate_mapping %s" % (self.doc_class_str, datetime.utcnow().strftime('%m/%d/%Y'))
        app_pillow.default_mapping = m
        if hasattr(app_pillow, '_calc_meta'):
            delattr(app_pillow, '_calc_meta')
        output = []
        output.append('APP_INDEX="%s_%s"' % (app_pillow.es_index_prefix, app_pillow.calc_meta()))
        output.append('APP_MAPPING=%s' % pprint.pformat(m))
        newcalc_index = "%s_%s" % (app_pillow.es_index_prefix, app_pillow.calc_meta())
        print "Writing new application index and mapping: %s" % output[0]
        with open(filepath, 'w') as outfile:
            outfile.write('\n'.join(output))

        if newcalc_index not in aliased_indices and newcalc_index != current_index:
            sys.stderr.write("\n\tWarning, current index %s is not aliased at the moment\n" % current_index)
            sys.stderr.write("\tCurrent live aliased index: %s\n\n"  % (','.join(aliased_indices)))

        sys.stderr.write("File written to %s\n" % filepath)
