import urllib
import urlparse
import logging
import requests
import re
import json
import uuid
import math
import os

from pylons import config

from ckan import plugins
from ckan import logic

from ckan.lib.navl.validators import not_empty

from ckan.plugins.core import SingletonPlugin, implements
from ckanext.harvest.interfaces import IHarvester
from ckan import model
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObjectExtra as HOExtra


class ESRIHarvester(HarvesterBase, SingletonPlugin):
    implements(IHarvester)

    # map crappy esri projections
    projMap = {
        104199 : "4326",
        102100 : "3857"
    }
    caMax = [-125.0, 42.5]
    caMin = [-113.0, 32.5]

    bad = []
    count = 0

    force_import = False

    _user_name = None

    def info(self):
        '''
        Harvesting implementations must provide this method, which will return a
        dictionary containing different descriptors of the harvester. The
        returned dictionary should contain:

        * name: machine-readable name. This will be the value stored in the
          database, and the one used by ckanext-harvest to call the appropiate
          harvester.
        * title: human-readable name. This will appear in the form's select box
          in the WUI.
        * description: a small description of what the harvester does. This will
          appear on the form as a guidance to the user.

        A complete example may be::

            {
                'name': 'csw',
                'title': 'CSW Server',
                'description': 'A server that implements OGC's Catalog Service
                                for the Web (CSW) standard'
            }

        :returns: A dictionary with the harvester descriptors
        '''
        return {
            'name'  : 'esri',
            'title' : 'ESRI ArcGIS Server',
            'description' : 'A ESRI ArcGIS Server, using Restful services'
        }

    def validate_config(self, config):
        '''

        [optional]

        Harvesters can provide this method to validate the configuration entered in the
        form. It should return a single string, which will be stored in the database.
        Exceptions raised will be shown in the form's error messages.

        :param harvest_object_id: Config string coming from the form
        :returns: A string with the validated configuration options
        '''

    def get_original_url(self, harvest_object_id):
        '''

        [optional]

        This optional but very recommended method allows harvesters to return
        the URL to the original remote document, given a Harvest Object id.
        Note that getting the harvest object you have access to its guid as
        well as the object source, which has the URL.
        This URL will be used on error reports to help publishers link to the
        original document that has the errors. If this method is not provided
        or no URL is returned, only a link to the local copy of the remote
        document will be shown.

        Examples:
            * For a CKAN record: http://{ckan-instance}/api/rest/{guid}
            * For a WAF record: http://{waf-root}/{file-name}
            * For a CSW record: http://{csw-server}/?Request=GetElementById&Id={guid}&...

        :param harvest_object_id: HarvestObject id
        :returns: A string with the URL to the original document
        '''
        obj = model.Session.query(HarvestObject).\
                                    filter(HarvestObject.id==harvest_object_id).\
                                    first()

        parts = urlparse.urlparse(obj.source.url)

        return obj.source.url


    def gather_stage(self, harvest_job):
        '''
        The gather stage will recieve a HarvestJob object and will be
        responsible for:
            - gathering all the necessary objects to fetch on a later.
              stage (e.g. for a CSW server, perform a GetRecords request)
            - creating the necessary HarvestObjects in the database, specifying
              the guid and a reference to its job. The HarvestObjects need a
              reference date with the last modified date for the resource, this
              may need to be set in a different stage depending on the type of
              source.
            - creating and storing any suitable HarvestGatherErrors that may
              occur.
            - returning a list with all the ids of the created HarvestObjects.

        :param harvest_job: HarvestJob object
        :returns: A list of HarvestObject ids
        '''
        log = logging.getLogger(__name__ + '.ESRIHarvester.gather')
        log.debug('ESRIHarvester gather_stage for job: %r', harvest_job)
        # Get source URL
        url = harvest_job.source.url

        #TODO: what's this?
        #self._set_source_config(harvest_job.source.config)

        # get the current ids?
        query = model.Session.query(HarvestObject.guid, HarvestObject.package_id).\
                                    filter(HarvestObject.current==True).\
                                    filter(HarvestObject.harvest_source_id==harvest_job.source.id)
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = set(guid_to_package_id.keys())

        log.debug('Starting gathering for %s' % url)
        guids_in_harvest = set()
        try:
            services = self._walk_argis_server(url)
            for service in services:
                try:
                    log.info('Found service %s from the ArcGIS Server', service)

                    guids_in_harvest.add(service)
                except Exception, e:
                    self._save_gather_error('Error for the service %s [%r]' % (service,e), harvest_job)
                    continue


        except Exception, e:
            log.error('Exception: %s' % e)
            self._save_gather_error('Error gathering the identifiers from the ArcGIS server [%s]' % str(e), harvest_job)
            return None

        new = guids_in_harvest - guids_in_db
        delete = guids_in_db - guids_in_harvest
        change = guids_in_db & guids_in_harvest

        ids = []
        for guid in new:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                extras=[HOExtra(key='status', value='new')])
            obj.save()
            ids.append(obj.id)
        for guid in change:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='change')])
            obj.save()
            ids.append(obj.id)
        for guid in delete:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='delete')])
            ids.append(obj.id)
            model.Session.query(HarvestObject).\
                  filter_by(guid=guid).\
                  update({'current': False}, False)
            obj.save()

        if len(ids) == 0:
            self._save_gather_error('No services found for the ArcGIS Server', harvest_job)
            return None

        return ids

    def fetch_stage(self, harvest_object):
        '''
        The fetch stage will receive a HarvestObject object and will be
        responsible for:
            - getting the contents of the remote object (e.g. for a CSW server,
              perform a GetRecordById request).
            - saving the content in the provided HarvestObject.
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - returning True if everything went as expected, False otherwise.

        :param harvest_object: HarvestObject object
        :returns: True if everything went right, False if errors were found
        '''
        log = logging.getLogger(__name__ + '.ESRIHarvester.fetch')
        log.debug('ESRIHarvester fetch_stage for object: %s', harvest_object.id)

        url = harvest_object.source.url

        # this is just the complete url to the service
        identifier = harvest_object.guid

        try:
            json = self._get_service(identifier)

            if json is None:
                self._save_object_error('Empty record for GUID %s' % identifier,
                                        harvest_object)
                return False

            harvest_object.content = json
            harvest_object.save()
        except Exception,e:
            self._save_object_error('Error saving the harvest object for GUID %s [%r]' % \
                                    (identifier, e), harvest_object)
            return False

        return True

    def import_stage(self, harvest_object):
        '''
        The import stage will receive a HarvestObject object and will be
        responsible for:
            - performing any necessary action with the fetched object (e.g
              create a CKAN package).
              Note: if this stage creates or updates a package, a reference
              to the package should be added to the HarvestObject.
            - creating the HarvestObject - Package relation (if necessary)
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - returning True if everything went as expected, False otherwise.

        :param harvest_object: HarvestObject object
        :returns: True if everything went right, False if errors were found
        '''

        log = logging.getLogger(__name__ + '.import')
        log.debug('Import stage for harvest object: %s', harvest_object.id)

        if not harvest_object:
            log.error('No harvest object received')
            return False


        if self.force_import:
            status = 'change'
        else:
            status = self._get_object_extra(harvest_object, 'status')

        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
                          .filter(HarvestObject.guid==harvest_object.guid) \
                          .filter(HarvestObject.current==True) \
                          .first()

        if status == 'delete':
            # Delete package
            context = {'model': model, 'session': model.Session, 'user': self._get_user_name()}

            plugins.toolkit.get_action('package_delete')(context, {'id': harvest_object.package_id})
            log.info('Deleted package {0} with guid {1}'.format(harvest_object.package_id, harvest_object.guid))

            return True

        # Parse
        try:
            jso = json.loads(harvest_object.content)
        except Exception, e:
            self._save_object_error('Error parsing service JSON for object {0}: {1}'.format(harvest_object.id, str(e)),
                                    harvest_object, 'Import')
            return False

        # Flag previous object as not current anymore
        if previous_object and not self.force_import:
            previous_object.current = False
            previous_object.add()


        # Build the package dict
        package_dict = self.get_package_dict(jso, harvest_object)
        if not package_dict:
            log.error('No package dict returned, aborting import for object {0}'.format(harvest_object.id))
            return False

        # Create / update the package

        context = {'model': model,
                   'session': model.Session,
                   'user': self._get_user_name(),
                   'extras_as_string': True,
                   'api_version': '2',
                   'return_id_only': True}
        if context['user'] == self._site_user['name']:
            context['ignore_auth'] = True


        # The default package schema does not like Upper case tags
        tag_schema = logic.schema.default_tags_schema()
        tag_schema['name'] = [not_empty, unicode]

        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()

        if status == 'new':
            package_schema = logic.schema.default_create_package_schema()
            package_schema['tags'] = tag_schema
            context['schema'] = package_schema

            # We need to explicitly provide a package ID, otherwise ckanext-spatial
            # won't be be able to link the extent to the package.
            package_dict['id'] = unicode(uuid.uuid4())
            package_schema['id'] = [unicode]

            # Save reference to the package on the object
            harvest_object.package_id = package_dict['id']
            harvest_object.add()
            # Defer constraints and flush so the dataset can be indexed with
            # the harvest object id (on the after_show hook from the harvester
            # plugin)
            model.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
            model.Session.flush()

            try:
                package_id = plugins.toolkit.get_action('package_create')(context, package_dict)
                log.info('Created new package %s with guid %s', package_id, harvest_object.guid)
            except plugins.toolkit.ValidationError, e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False

        elif status == 'change':

            # Check if the modified date is more recent
            if not self.force_import and harvest_object.metadata_modified_date <= previous_object.metadata_modified_date:

                # Assign the previous job id to the new object to
                # avoid losing history

                # JM - TODO: this was throwing errors about object not being bound to session
                #harvest_object.harvest_job_id = previous_object.job.id
                harvest_object.add()

                # Delete the previous object to avoid cluttering the object table
                previous_object.delete()

                log.info('Document with GUID %s unchanged, skipping...' % (harvest_object.guid))
            else:
                package_schema = logic.schema.default_update_package_schema()
                package_schema['tags'] = tag_schema
                context['schema'] = package_schema

                package_dict['id'] = harvest_object.package_id
                try:
                    package_id = plugins.toolkit.get_action('package_update')(context, package_dict)
                    log.info('Updated package %s with guid %s', package_id, harvest_object.guid)
                except plugins.toolkit.ValidationError, e:
                    self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                    return False

        model.Session.commit()

        return True


    # STOLEN HELPERS - mostly from the ckanext-spatial
    def _get_user_name(self):
        '''
        Returns the name of the user that will perform the harvesting actions
        (deleting, updating and creating datasets)

        By default this will be the internal site admin user. This is the
        recommended setting, but if necessary it can be overridden with the
        `ckanext.spatial.harvest.user_name` config option, eg to support the
        old hardcoded 'harvest' user:

           ckanext.spatial.harvest.user_name = harvest

        '''
        if self._user_name:
            return self._user_name

        self._site_user = plugins.toolkit.get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})

        config_user_name = config.get('ckanext.spatial.harvest.user_name')
        if config_user_name:
            self._user_name = config_user_name
        else:
            self._user_name = self._site_user['name']

        return self._user_name

    def get_package_dict(self, jso, harvest_object):
        '''
        Constructs a package_dict suitable to be passed to package_create or
        package_update. See documentation on
        ckan.logic.action.create.package_create for more details

        Tipically, custom harvesters would only want to add or modify the
        extras, but the whole method can be replaced if necessary. Note that
        if only minor modifications need to be made you can call the parent
        method from your custom harvester and modify the output, eg:

            class MyHarvester(SpatialHarvester):

                def get_package_dict(self, iso_values, harvest_object):

                    package_dict = super(MyHarvester, self).get_package_dict(iso_values, harvest_object)

                    package_dict['extras']['my-custom-extra-1'] = 'value1'
                    package_dict['extras']['my-custom-extra-2'] = 'value2'

                    return package_dict

        If a dict is not returned by this function, the import stage will be cancelled.

        :param iso_values: Dictionary with parsed values from the ISO 19139
            XML document
        :type iso_values: dict
        :param harvest_object: HarvestObject domain object (with access to
            job and source objects)
        :type harvest_object: HarvestObject

        :returns: A dataset dictionary (package_dict)
        :rtype: dict
        '''

        #tags = []
        #if 'tags' in iso_values:
        #    for tag in iso_values['tags']:
        #        tag = tag[:50] if len(tag) > 50 else tag
        #        tags.append({'name': tag})

        url = re.sub('\?.*','',harvest_object.guid).split('/')
        type = url[len(url)-1]
        serviceName = url[len(url)-2]

        package_dict = {
            'title': self._get_name(jso, type, serviceName),
            'notes' : self._get_description(jso),
            'tags': [],
            'resources': [{
                'url' : harvest_object.guid,
                'format' : 'Map Service',
                'resource_type' : type,
                'name' : 'Map Service'
            }],
        }

        # We need to get the owner organization (if any) from the harvest
        # source dataset
        source_dataset = model.Package.get(harvest_object.source.id)
        if source_dataset.owner_org:
            package_dict['owner_org'] = source_dataset.owner_org

        # Package name
        package = harvest_object.package
        if package is None or package.title != package_dict['title']:
            name = self._gen_new_name(package_dict['title'])
            if not name:
                name = self._gen_new_name(str(package_dict['guid']))
            if not name:
                raise Exception('Could not generate a unique name from the title or the GUID. Please choose a more unique title.')
            package_dict['name'] = name
        else:
            package_dict['name'] = package.name

        extras = {
            'guid': harvest_object.guid,
            'esri_harvester': True,
            'spatial' : self._get_extent(jso)
        }

        extras_as_dict = []
        for key, value in extras.iteritems():
            if isinstance(value, (list, dict)):
                extras_as_dict.append({'key': key, 'value': json.dumps(value)})
            else:
                extras_as_dict.append({'key': key, 'value': value})

        package_dict['extras'] = extras_as_dict

        return package_dict

    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None




    # ESRI CRAWLER HELPERS
    def _walk_argis_server(self, url):
        p1 = re.split('://', url)
        p2 = re.split('/', p1[1])

        server = p1[0]+"://"+p2[0]
        p2.pop(0)
        path = '/'.join(p2)

        services = []
        self._walk_folder(server, path, "", services)
        return services

    def _get_json(self, url):
        if not re.match('.*?f=json.*', url):
            url = url + '?f=json'

        r = requests.get(url, stream=True)
        return r.json()

    def _walk_folder(self, server, path, foldername, services):
        log = logging.getLogger(__name__ + '.ESRIHarvester.gather')
        server = server.strip('/')
        path = path.strip('/')

        try:
            json = self._get_json(server+"/"+path+"/"+foldername)
        except:
            log.debug('Failed to access folder: ' % server+"/"+path+"/"+foldername)

        serviceList = json.get("services")
        for service in serviceList:
            serviceUrl = server+"/"+path+"/"+service.get("name")+"/"+service.get("type")


            try:
                serviceJson = self._get_json(serviceUrl)
                if self._is_ca(serviceJson):
                    services.append(serviceUrl)
                    log.debug('Service is in CA:  %s' % serviceUrl)
                else:
                    log.debug('Service is OUTSIDE CA:  %s' % serviceUrl)
            except:
                log.debug('Failed to access service: ' % serviceUrl)



        folders = json.get("folders")
        for folder in folders:
            self._walk_folder(server, path+"/"+foldername, folder, services)

    def _get_service(self, url):
        if not re.match('.*?f=json.*', url):
            url = url + '?f=json'
        r = requests.get(url, stream=True)
        return r.text

    def _get_name(self, json, type, serviceName):
        if type == "MapServer":
            mapName = json.get("mapName")
            if mapName == "" or mapName == "Layers" or mapName == None:
                if json.get("documentInfo") == None:
                    return re.sub('_', ' ', serviceName)
                elif json.get("documentInfo").get("Title") == None or json.get("documentInfo").get("Title") == "":
                    return re.sub('_', ' ', serviceName)
                else:
                    return json.get("documentInfo").get("Title").strip()
            else:
                return mapName.strip()

        return type

    def _get_description(self, json):
        if json.get("serviceDescription") != None and json.get("serviceDescription") != "":
            return json.get("serviceDescription")

        if json.get("description") != None and json.get("description") != "":
            return json.get("description")

    def _get_extent(self, json):
        extentVars = ["fullExtent", "initialExtent", "extent"]
        hasExtent = False

        for extentVar in extentVars:
            if json.get(extentVar) != None:
                if self._is_ext_ca(json.get(extentVar)):
                    return self._format_geojson(json.get(extentVar))

        return {}

    def _format_geojson(self, ext):
        sr = ext.get("spatialReference")
        if sr.get("wkid") != None:
            try:
                br = self._transform(sr.get("wkid"), "4326", ext.get("xmax"), ext.get("ymin"))
                tl = self._transform(sr.get("wkid"), "4326", ext.get("xmin"), ext.get("ymax"))

                return {
                    "type": "Polygon",
                    "coordinates": [[
                        [tl[0], tl[1]],
                        [tl[0], br[1]],
                        [br[0], br[1]],
                        [br[0], tl[1]]
                    ]]
                }


            except Exception as e:
                print Exception, e
                print "Error projecting:  %s %s %s" % (sr.get("wkid"), ext.get("xmin"), ext.get("ymin"))
                return False

        return {}


    def _is_ca(self, json):
        extentVars = ["fullExtent", "initialExtent", "extent"]
        hasExtent = False

        for extentVar in extentVars:
            if json.get(extentVar) != None:
                hasExtent = True
                #print 'Checking %s' % (extentVar)
                if self._is_ext_ca(json.get(extentVar)):
                    return True

        if hasExtent:
            return False

        return False

    def _is_ext_ca(self, ext):
        sr = ext.get("spatialReference")
        if sr.get("wkid") != None:
            try:
                min = self._transform(sr.get("wkid"), "4326", ext.get("xmax"), ext.get("ymin"))
                max = self._transform(sr.get("wkid"), "4326", ext.get("xmin"), ext.get("ymax"))

                # check to see if we have real numbers
                if not self._check_valid(min, max):
                    return False

                if self._intersect(self.caMin, self.caMax, min, max):
                    return True
                elif self._intersect(min, max, self.caMin, self.caMax):
                    return True
                else:
                    # we only return false when we can validate it's outside of california
                    return False

            except Exception as e:
                print Exception, e
                print "Error projecting:  %s %s %s" % (sr.get("wkid"), ext.get("xmin"), ext.get("ymin"))
                return False
        return False

    def _check_valid(self, br, tl):
        if math.isnan(br[0]) or math.isnan(br[1]) or math.isnan(tl[0]) or math.isnan(tl[1]):
            return False
        return True

    def _intersect(self, min1, max1, br, tl):
        if self._point_intersect(min1[0], min1[1], br, tl):
            return True
        elif self._point_intersect(min1[0], max1[1], br, tl):
            return True
        elif self._point_intersect(max1[0], min1[1], br, tl):
            return True
        elif self._point_intersect(max1[0], max1[1], br, tl):
            return True
        return False

    def _point_intersect(self, x, y, br, tl):
        #print "%s < %s and %s > %s and %s > %s and %s < %s" % (x, br[0], x, tl[0], y, br[1], y,tl[1])
        #print "    %s" % (x < br[0] and x > tl[0] and y > br[1] and y < tl[1])
        #print "%s and %s and %s and %s" % ((x < br[0]), (x > tl[0]), (y > br[1]), (y < tl[1]))
        if x < br[0] and x > tl[0] and y > br[1] and y < tl[1]:
            return True
        return False

    def _transform(self, p1, p2, x, y):
        if p1 in self.projMap:
            p1 = self.projMap[p1]

        #print "echo '%s %s' | gdaltransform -s_srs EPSG:%s -t_srs EPSG:%s" % (x, y, p1, p2)
        #print os.popen("echo '%s %s' | gdaltransform -s_srs EPSG:%s -t_srs EPSG:%s" % (x, y, p1, p2)).read()
        parts = os.popen("echo '%s %s' | gdaltransform -s_srs EPSG:%s -t_srs EPSG:%s" % (x, y, p1, p2)).read().split(" ")
        return [float(parts[0]), float(parts[1])]