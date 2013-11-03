from django.conf import settings
from corehq.apps.hqadmin.management.commands.make_supervisor_conf import SupervisorConfCommand


class Command(SupervisorConfCommand):
    help = "Make pillowtop supervisord conf - multiple configs per the PILLOWTOPS setting"
    args = ""

    def render_configuration_file(self, conf_template_string):
        """
        Hacky override to make pillowtop config. Multiple configs within the conf file
        """
        configs = []
        all_pillows = [pillow for group_key, items in settings.PILLOWTOPS.items() for pillow in items]
        for full_name in all_pillows:
            pillow_name = full_name.split('.')[-1]
            pillow_params = {
                'pillow_name': pillow_name,
                'pillow_option': ' --pillow-name %s' % pillow_name
            }
            pillow_params.update(self.params)
            pillow_rendering = conf_template_string % pillow_params
            configs.append(pillow_rendering)
        return '\n\n'.join(configs)
