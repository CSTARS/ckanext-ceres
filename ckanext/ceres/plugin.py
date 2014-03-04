import logging
import os
import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.model as model
import ckan.lib.navl.dictization_functions as df
from ckan.logic.validators import tag_in_vocabulary_validator
from ckan.common import _

from ckan.logic.converters import convert_to_extras, convert_from_extras, convert_to_tags, convert_from_tags
from ckan.lib.navl.validators import ignore_missing


# FIXME OrderedDict should be available via the toolkit
try:
    from collections import OrderedDict # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict


# JM
def Topic():
    '''Return the topics to the UI.'''
    try:
        topics = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'Topic'})
        return topics
    except tk.ObjectNotFound:
        return None

def Partners():
    '''Return the partners to the UI.'''
    try:
        partners = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'Partner'})
        return partners
    except tk.ObjectNotFound:
        return None

# JM
# for our custom tags, the convert_from_tags returns a array which is nasty
# to the ui. If is array is return, join to create comma sepeated string
# NOTE: this function needs to be called AFTER calling convert_from_tags
def listToString(key, data, errors, context):
    for k in data.keys():
        if k[0] == key[0] and not isinstance(data[k], str):
            print "%s %s" % (k, data[k])
            data[k] = ', '.join(data[k])

# JM
# HACK: the helper function fails to split comma seperated tag strings
# returned by the tag widget! Overriding to handle this case
def convert_to_tags_custom(vocab):
    def callable(key, data, errors, context):
        new_tags = data.get(key)
        if not new_tags:
            return
        if isinstance(new_tags, basestring):
            new_tags = [new_tags]

        # get current number of tags
        n = 0
        for k in data.keys():
            if k[0] == 'tags':
                n = max(n, k[1] + 1)

        v = model.Vocabulary.get(vocab)
        if not v:
            raise df.Invalid(_('Tag vocabulary "%s" does not exist') % vocab)
        context['vocabulary'] = v

        for tag in new_tags:
            for part in tag.split(","):
                try:
                    tag_in_vocabulary_validator(part, context)
                except Exception:
                    print "need to create tag"

        num = 1;
        for i, tag in enumerate(new_tags):
            for part in tag.split(","):
                data[('tags', num + n, 'name')] = part
                data[('tags', num + n, 'vocabulary_id')] = v.id
                num += 1
    return callable

# JM
def escape_json(str):
    try:
        return json.dumps(str)
    except Exception:
        return "\"\""

class CeresPlugin(plugins.SingletonPlugin,
        tk.DefaultDatasetForm):
    '''An example IDatasetForm CKAN plugin.

    Uses a tag vocabulary to add a custom metadata field to datasets.

    '''
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    def after_map(self, map):
        map.connect('clogin', '/clogin',
            controller='ckanext.ceres.controller:CeicController',
            action='index')
        map.connect('clogin_action', '/clogin/{action}',
            controller='ckanext.ceres.controller:CeicController')
        return map


    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')
        # setting up Fanstatic directory.  In here you will find a resource.config file
        tk.add_resource('public','ceres')

    # Used by ITemplateHelpers to provide data to frontend
    def get_helpers(self):
        return {'Topic':Topic,
                'Partners':Partners,
                'escape_json' : escape_json
                }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        #schema.update({
        #        'access_level': [tk.get_validator('ignore_missing'),
        #            tk.get_converter('convert_to_tags')('access_levels')]
        #        })

        # Add custom access_level as extra field

        
        schema.update({
            'Topic': [convert_to_tags_custom('Topic'), ignore_missing]
        })


        '''schema.update({
                'pkg_type': [tk.get_converter('convert_to_extras'), tk.get_validator('ignore_missing')]
        })

        schema.update({
                'Contributor': [
                           convert_to_tags('Contributor'),
                           tk.get_validator('ignore_missing')]
                })

        schema.update({
                'contributing_org': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        # Add custom granularity as extra field
        schema.update({
                'locations': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'data_contact': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'distribution_contact': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'metadata_contact': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'other_contact': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'purpose': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'progress': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'currentness': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'spatial': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'update_frequency': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })

        schema.update({
                'use_constraints': [tk.get_validator('ignore_missing'),
                    tk.get_converter('convert_to_extras')]
                })'''

        return schema

    def create_package_schema(self):
        schema = super(CeresPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(CeresPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(CeresPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add our custom access_level metadata field to the schema.

        schema.update({
            'Topic': [
                       convert_from_tags('Topic'),
                       listToString,
                       ignore_missing]
            })

        '''schema.update({
            'pkg_type': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        

        
        schema.update({
            'contributing_org': [
                    tk.get_converter('convert_from_extras'),
                    tk.get_validator('ignore_missing')
                ]
            })

        # Add our systemOfRecords field to the dataset schema.
        schema.update({
            'locations': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'data_contact': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'distribution_contact': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'metadata_contact': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'other_contact': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })

        # Add our granularity field to the dataset schema.
        schema.update({
            'purpose': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'progress': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'currentness': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'spatial': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        
        schema.update({
            'update_frequency': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })
        
        schema.update({
            'use_constraints': [tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
            })'''

        return schema


    # These methods just record how many times they're called, for testing
    # purposes.
    # TODO: It might be better to test that custom templates returned by
    # these methods are actually used, not just that the methods get
    # called.

    def setup_template_variables(self, context, data_dict):
        return super(CeresPlugin, self).setup_template_variables(
                context, data_dict)

    def new_template(self):
        return super(CeresPlugin, self).new_template()

    def read_template(self):
        return super(CeresPlugin, self).read_template()

    def edit_template(self):
        return super(CeresPlugin, self).edit_template()

    def comments_template(self):
        return super(CeresPlugin, self).comments_template()

    def search_template(self):
        return super(CeresPlugin, self).search_template()

    def history_template(self):
        return super(CeresPlugin, self).history_template()

    def package_form(self):
        return super(CeresPlugin, self).package_form()

    # check_data_dict() is deprecated, this method is only here to test that
    # legacy support for the deprecated method works.
    def check_data_dict(self, data_dict, schema=None):
        return

