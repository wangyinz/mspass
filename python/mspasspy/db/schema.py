"""
Tools to define the schema of Metadata.
"""
import os

import yaml
from schema import Schema, Or, Optional, SchemaError
import bson.objectid

from mspasspy.ccore.utility import MsPASSError

class SchemaBase:
    def __init__(self, schema_file=None):
        if schema_file is None and 'MSPASS_HOME' in os.environ:
            schema_file = os.path.abspath(os.environ['MSPASS_HOME']) + '/data/yaml/mspass.yaml'
        else:
            schema_file = os.path.abspath(os.path.dirname(__file__) + '/../data/yaml/mspass.yaml')
        try:
            with open(schema_file, 'r') as stream:
                    schema_dic = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            raise MsPASSError('Cannot parse schema definition file: ' + schema_file, 'Fatal') from e
        except EnvironmentError as e:
            raise MsPASSError('Cannot open schema definition file: ' + schema_file, 'Fatal') from e

        try:
            _check_format(schema_dic)
        except SchemaError as e:
            raise MsPASSError('The schema definition is not valid', 'Fatal') from e
        self._raw = schema_dic

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as ae:
            raise MsPASSError('The schema of ' + key + ' is not defined', 'Invalid') from ae

    def __delitem__(self, key):
        try:
            return delattr(self, key)
        except AttributeError as ae:
            raise MsPASSError('The schema of ' + key + ' is not defined', 'Invalid') from ae

class SchemaDefinitionBase:
    _main_dic = {}
    _alias_dic = {}
    def add(self, name, attr):
        """
        Add a new entry to the definitions. Note that because the internal
        container is `dict` if attribute for name is already present it
        will be silently replaced.

        :param name: The name of the attribute to be added
        :type name: str
        :param attr: A dictionary that defines the property of the added attribute.
            Note that the type must be defined.
        :type attr: dict
        :raises mspasspy.ccore.utility.MsPASSError: if type is not defined in attr
        """
        if 'type' not in attr:
            raise MsPASSError('type is not defined for the new attribute', 'Invalid')
        self._main_dic[name] = attr
        if 'aliases' in attr:
            for als in attr['aliases']:
                self._alias_dic[als] = name

    def add_alias(self, key, aliasname):
        """
        Add an alias for key

        :param key: key to be added
        :type key: str
        :param aliasname: aliasname to be added
        :type aliasname: str
        """
        self._main_dic[key]['aliases'].append(aliasname)
        self._alias_dic[aliasname] = key

    def aliases(self, key):
        """
        Get a list of aliases for a given key.

        :param key: The unique key that has aliases defined.
        :type key: str
        :return: A list of aliases associated to the key.
        :rtype: list
        """
        return None if 'aliases' not in self._main_dic[key] else self._main_dic[key]['aliases']

    # TODO def apply_aliases

    def clear_aliases(self, md):
        """
        Restore any aliases to unique names.

        Aliases are needed to support legacy packages, but can cause downstream problem
        if left intact. This method clears any aliases and sets them to the unique_name
        defined by this object. Note that if the unique_name is already defined, it will
        silently remove the alias only.

        :param md: Data object to be altered. Normally a class:`mspasspy.ccore.seismic.Seismogram`
            or class:`mspasspy.ccore.seismic.TimeSeries` but can be a raw class:`mspasspy.ccore.utility.Metadata`.
        :type md: class:`mspasspy.ccore.utility.Metadata`
        """
        for key in md.keys():
            if self.is_alias(key):
                if self.unique_name(key) not in md:
                    md.change_key(key, self.unique_name(key))
                else:
                    del md[key]  

    def concept(self, key):
        """
        Return a description of the concept this attribute defines.

        :param key: The name that defines the attribute of interest
        :type key: str
        :return: A string with a terse description of the concept this attribute defines
        :rtype: str
        :raises mspasspy.ccore.utility.MsPASSError: if concept is not defined
        """
        if 'concept' not in self._main_dic[key]:
            raise MsPASSError('concept is not defined for ' + key, 'Complaint')
        return self._main_dic[key]['concept']

    def has_alias(self, key):
        """
        Test if a key has registered aliases

        Sometimes it is helpful to have alias keys to define a common concept.
        For instance, if an attribute is loaded from a relational db one might
        want to use alias names of the form table.attribute as an alias to
        attribute. has_alias should be called first to establish if a name has
        an alias. To get a list of aliases call the aliases method.

        :param key: key to be tested
        :type key: str
        :return: `True` if the key has aliases, else or if key is not defined return `False`
        :rtype: bool
        """
        return key in self._main_dic and 'aliases' in self._main_dic[key]

    def is_alias(self, key):
        """
        Test if a key is a registered alias

        This asks the inverse question to has_alias. That is, it yields true of the key is
        registered as a valid alias. It returns false if the key is not defined at all. Note
        it will yield false if the key is a registered unique name and not an alias.

        :param key: key to be tested
        :type key: str
        :return: `True` if the key is a alias, else return `False`
        :rtype: bool
        """
        return key in self._alias_dic

    def is_defined(self, key):
        """
        Test if a key is defined either as a unique key or an alias

        :param key: key to be tested
        :type key: str
        :return: `True` if the key is defined
        :rtype: bool
        """
        return key in self._main_dic or key in self._alias_dic

    def is_optional(self, key):
        """
        Test if a key is optional to the schema

        :param key: key to be tested
        :type key: str
        :return: `True` if the key is optional
        :rtype: bool
        """
        return False if 'optional' not in self._main_dic[key] else self._main_dic[key]['optional']

    def keys(self):
        """
        Get a list of all the unique keys defined.

        :return: list of all the unique keys defined
        :rtype: list
        """
        return self._main_dic.keys()

    def type(self, key):
        """
        Return the type of an attribute. If not recognized, it returns None.

        :param key: The name that defines the attribute of interest
        :type key: str
        :return: type of the attribute associated with ``key``
        :rtype: class:`type`
        """
        tp = self._main_dic[key]['type'].strip().casefold()
        if tp in ['int', 'integer']:
            return int
        if tp in ['double', 'float']:
            return float
        if tp in ['str', 'string']:
            return str
        if tp in ['bool', 'boolean']:
            return bool
        if tp in ['dict']:
            return dict
        if tp in ['list']:
            return list
        if tp in ['objectid']:
            return bson.objectid.ObjectId
        if tp in ['bytes', 'byte', 'object']:
            return bytes
        return None

    def unique_name(self, aliasname):
        """
        Get definitive name for an alias.

        This method is used to ask the opposite question as aliases. The aliases method
        returns all acceptable alternatives to a definitive name defined as the key to
        get said list. This method asks what definitive key should be used to fetch an
        attribute. Note that if the input is already the unique name, it will return itself.

        :param aliasname: the name of the alias for which we want the definitive key
        :type aliasname: str
        :return: the name of the definitive key
        :rtype: str
        :raises mspasspy.ccore.utility.MsPASSError: if aliasname is not defined
        """
        if aliasname in self._main_dic:
            return aliasname
        if aliasname in self._alias_dic:
            return self._alias_dic[aliasname]
        raise MsPASSError(aliasname + ' is not defined', 'Invalid')

class DatabaseSchema(SchemaBase):
    def __init__(self, schema_file=None):
        super().__init__(schema_file)
        self._default_dic = {}
        for collection in self._raw['Database']:
            setattr(self, collection, DBSchemaDefinition(self._raw['Database'], collection))
            if 'default' in self._raw['Database'][collection]:
                self._default_dic[self._raw['Database']
                [collection]['default']] = collection

    def __setitem__(self, key, value):
        if not isinstance(value, DBSchemaDefinition):
            raise MsPASSError('value is not a DBSchemaDefinition', 'Invalid')
        setattr(self, key, value)

    def default(self, name):
        """
        Return the schema definition of a default collection.

        This method is used when multiple collections of the same concept is defined.
        For example, the wf_TimeSeries and wf_Seismogram are both collections that
        are used for data objects (characterized by their common wf prefix). The
        Database API needs a default wf collection to operate on when no collection
        name is explicitly given. In this case, this default_name method can be used.
        Note that if requested name has no default collection defined and it is a
        defined collection, it will treat that collection itself as the default.

        :param name: The requested default collection
        :type name: str
        :return: the schema definition of the default collection
        :rtype: class:`mspasspy.db.schema.DBSchemaDefinition`
        :raises mspasspy.ccore.utility.MsPASSError: if the name has no default defined
        """
        if name in self._default_dic:
            return getattr(self, self._default_dic[name])
        if name in self._raw['Database']:
            return getattr(self, name)
        raise MsPASSError(name + ' has no default defined', 'Invalid')

    def default_name(self, name):
        """
        Return the name of a default collection.

        This method is behaves similar to the default method, but it only returns the
        name as a string instead.

        :param name: The requested default collection
        :type name: str
        :return: the name of the default collection
        :rtype: str
        :raises mspasspy.ccore.utility.MsPASSError: if the name has no default defined
        """
        if name in self._default_dic:
            return self._default_dic[name]
        if name in self._raw['Database']:
            return name
        raise MsPASSError(name + ' has no default defined', 'Invalid')

    def set_default(self, collection: str, default: str=None):
        """
        Set a collection as the default.

        This method is used to change the default collections (e.g., switching between
        wf_TimeSeries and wf_Seismogram). If ``default`` is not given, it will try to
        infer one from ``collection`` at the first occurrence of "_"
        (e.g., wf_TimeSeries will become wf).

        :param collection: The name of the targetting collection
        :type collection: str
        :param default: the default name to be set to
        :type default: str, optional
        """
        if not hasattr(self, collection):
            raise MsPASSError(collection + ' is not a defined collection', 'Invalid')
        if default is None:
            self._default_dic[collection.split("_", 1)[0]] = collection
        else:
            self._default_dic[default] = collection

    def unset_default(self, default: str):
        """
        Unset a default.

        This method does nothing if ``default`` is not defined.

        :param default: the default name to be unset
        :type default: str
        """
        if default in self._default_dic:
            self._default_dic.pop(default)

class DBSchemaDefinition(SchemaDefinitionBase):
    def __init__(self, schema_dic, collection_str):
        self._collection_str = collection_str
        if 'base' in schema_dic[collection_str]:
            base_def = DBSchemaDefinition(schema_dic, schema_dic[collection_str]['base'])
            self._main_dic = base_def._main_dic
            self._alias_dic = base_def._alias_dic
        else:
            self._main_dic = {}
            self._alias_dic = {}
        self._main_dic.update(schema_dic[collection_str]['schema'])
        for key, attr in self._main_dic.items():
            if 'reference' in attr:
                k = key
                if k == attr['reference'] + '_id':
                    k = '_id'
                refer_dic = schema_dic[attr['reference']]
                while 'base' in refer_dic:
                    refer_dic = schema_dic[refer_dic['base']]
                    if k in refer_dic['schema']:
                        break
                foreign_attr = refer_dic['schema'][k]
                # The order of below operation matters. The behavior is that we only
                # extend attr with items from foreign_attr that are not defined in attr.
                # This garantees that the foreign_attr won't overwrite attr's exisiting keys.
                compiled_attr = dict(list(foreign_attr.items()) + list(attr.items()))
                self._main_dic[key] = compiled_attr

            if 'aliases' in attr:
                self._alias_dic.update({item:key for item in attr['aliases']})

    def reference(self, key):
        """
        Return the collection name that a key is referenced from

        :param key: the name of the key
        :type key: str
        :return: the name of the collection
        :rtype: str
        :raises mspasspy.ccore.utility.MsPASSError: if the key is not defined
        """
        if key not in self._main_dic:
            raise MsPASSError(key + ' is not defined', 'Invalid')
        return self._collection_str if 'reference' not in self._main_dic[key] else self._main_dic[key]['reference']

class MetadataSchema(SchemaBase):
    def __init__(self, schema_file=None):
        super().__init__(schema_file)
        dbschema = DatabaseSchema(schema_file)
        for collection in self._raw['Metadata']:
            setattr(self, collection, MDSchemaDefinition(self._raw['Metadata'], collection, dbschema))
    def __setitem__(self, key, value):
        if not isinstance(value, MDSchemaDefinition):
            raise MsPASSError('value is not a MDSchemaDefinition', 'Invalid')
        setattr(self, key, value)


class MDSchemaDefinition(SchemaDefinitionBase):
    def __init__(self, schema_dic, collection_str, dbschema):
        if 'base' in schema_dic[collection_str]:
            base_def = MDSchemaDefinition(schema_dic, schema_dic[collection_str]['base'], dbschema)
            self._main_dic = base_def._main_dic
            self._alias_dic = base_def._alias_dic
        else:
            self._main_dic = {}
            self._alias_dic = {}
        self._main_dic.update(schema_dic[collection_str]['schema'])
        for key, attr in self._main_dic.items():
            if 'collection' in attr:
                s_key = key
                col_name = attr['collection']
                if key.startswith(col_name):
                    s_key = key.replace(col_name + '_', '')
                foreign_attr = getattr(dbschema,col_name)._main_dic[s_key]
                # The order of below operation matters. The behavior is that we only
                # extend attr with items from foreign_attr that are not defined in attr.
                # This garantees that the foreign_attr won't overwrite attr's exisiting keys.
                compiled_attr = dict(list(foreign_attr.items()) + list(attr.items()))
                self._main_dic[key] = compiled_attr

            if 'aliases' in self._main_dic[key]:
                self._alias_dic.update({item:key for item in self._main_dic[key]['aliases'] if item != key})

    def collection(self, key):
        """
        Return the collection name that a key belongs to

        :param key: the name of the key
        :type key: str
        :return: the name of the collection
        :rtype: str
        """
        return None if 'collection' not in self._main_dic[key] else self._main_dic[key]['collection']

    def readonly(self, key):
        """
        Check if an attribute is marked readonly.

        :param key: key to be tested
        :type key: str
        :return: `True` if the key is readonly or its readonly attribute is not defined, else return `False`
        :rtype: bool
        :raises mspasspy.ccore.utility.MsPASSError: if the key is not defined
        """
        if key not in self._main_dic:
            raise MsPASSError(key + ' is not defined', 'Invalid')
        return True if 'readonly' not in self._main_dic[key] else self._main_dic[key]['readonly']

    def writeable(self, key):
        """
        Check if an attribute is writeable. Inverted logic from the readonly method.

        :param key: key to be tested
        :type key: str
        :return: `True` if the key is not readonly, else or its readonly attribute is not defined return `False`
        :rtype: bool
        :raises mspasspy.ccore.utility.MsPASSError: if the key is not defined
        """
        return not self.readonly(key)

    def set_readonly(self, key):
        """
        Lock an attribute to assure it will not be saved.

        Parameters can be defined readonly. That is a standard feature of this class,
        but is normally expected to be set on construction of the object.
        There are sometimes reason to lock out a parameter to keep it from being
        saved in output. This method allows this. On the other hand, use this feature
        only if you fully understand the downstream implications or you may experience
        unintended consequences.

        :param key: the key for the attribute with properties to be redefined
        :type key: str
        :raises mspasspy.ccore.utility.MsPASSError: if the key is not defined
        """
        if key not in self._main_dic:
            raise MsPASSError(key + ' is not defined', 'Invalid')
        self._main_dic[key]['readonly'] = True

    def set_writeable(self, key):
        """
        Force an attribute to be writeable.

        Normally some parameters are marked readonly on construction to avoid
        corrupting the database with inconsistent data defined with a common
        key. (e.g. sta) This method overrides such definitions for any key so
        marked. This method should be used with caution as it could have
        unintended side effects.

        :param key: the key for the attribute with properties to be redefined
        :type key: str
        :raises mspasspy.ccore.utility.MsPASSError: if the key is not defined
        """
        if key not in self._main_dic:
            raise MsPASSError(key + ' is not defined', 'Invalid')
        self._main_dic[key]['readonly'] = False


'''
check if a mspass.yaml file is valid or not
'''
def _check_format(schema_dic):
    schema = {
        "Database":{
            "wf_TimeSeries":{
                Optional("default", default="wf"):str,
                "schema":{
                    "_id":{
                        "type":"ObjectID",
                        Optional("concept", default="ObjectId used to define a data object"):str
                    },
                    "npts":{
                        "type":"int",
                        Optional("concept", default="Number of data samples"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "delta":{
                        "type":"double",
                        Optional("concept", default="Data sample interval in seconds"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    Optional("sampling_rate"):{
                        "type":"double",
                        Optional("concept", default="Data sampling frequency in Hz=1/s"):str
                    },
                    "starttime":{
                        "type":"double",
                        Optional("concept", default="Time of first sample of data (epoch time or relative to some other time mark)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "starttime_shift":{
                        "type":"double",
                        Optional("concept", default="Time shift applied to define relative time of 0.0"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "utc_convertible":{
                        "type":"bool",
                        Optional("concept", default="When true starttime_shift can be used to convert relative time to UTC."):str
                    },
                    "time_standard":{
                        "type":"string",
                        Optional("concept", default="Defines time standard for meaning of t0 (default should be UTC)"):str
                    },
                    Optional("calib"):{
                        "type":"double",
                        Optional("concept", default="Nominal conversion factor for changing sample data to ground motion units."):str
                    },
                    "storage_mode":{
                        "type":"string",
                        Optional("concept", default="The storage mode of the saved data ('file', 'url' or 'gridfs')"):str
                    },
                    Optional("dir"):{
                        "type":"string",
                        Optional("concept", default="Directory path to an external file (always used with dfile)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    Optional("dfile"):{
                        "type":"string",
                        Optional("concept", default="External data file name."):str,
                        Optional("aliases"):Or(str, list)
                    },
                    Optional("foff"):{
                        "type":"int",
                        Optional("concept", default="Offset in bytes from beginning of a file to first data sample."):str,
                        Optional("aliases"):Or(str, list)
                    },
                    Optional("url"):{
                        "type":"string",
                        Optional("concept", default="Url to external data file."):str
                    },
                    Optional("gridfs_id"):{
                        "type":"ObjectID",
                        Optional("concept", default="The _id of data file in the fs.files collection."):str
                    },
                    "site_id":{
                        "reference":"site"
                    },
                    "channel_id":{
                        "reference":"channel"
                    },
                    Optional("source_id"):{
                        "reference":"source"
                    },
                    Optional("history_object_id"):{
                        "reference":"history_object"
                    },
                    Optional("elog_id"):{
                        "type":"list",
                        "reference":"elog"
                    }
                }
            },
            "wf_Seismogram":{
                "base":"wf_TimeSeries",
                "schema":{
                    "tmatrix":{
                        "type":"list",
                        Optional("concept", default="Three-component data's transformation matrix"):str
                    },
                    Optional("channel_id"):{
                        "type":"list",
                        "reference":"channel"
                    }
                }
            },
            "site":{
                "schema":{
                    "_id":{
                        "type":"ObjectID",
                        Optional("concept", default="ObjectId used to define a particular instrument/seismic station"):str
                    },
                    "net":{
                        "type":"string",
                        Optional("concept", default="network code (net component of SEED net:sta:chan)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "sta":{
                        "type":"string",
                        Optional("concept", default="station code assigned to a spot on Earth (sta component of SEED net:sta:chan)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    Optional("loc"):{
                        "reference":"channel"
                    },
                    "lat":{
                        "type":"double",
                        Optional("concept", default="latitude of a seismic station/instrument in degrees"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "lon":{
                        "type":"double",
                        Optional("concept", default="longitude of a seismic station/instrument in degrees"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "elev":{
                        "type":"double",
                        Optional("concept", default="elevation of a seismic station/instrument in km (subtract emplacement depth for borehole instruments)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "starttime":{
                        "type":"double",
                        Optional("concept", default="Time of seismic station/instrument starts recording"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "endtime":{
                        "type":"double",
                        Optional("concept", default="Time of seismic station/instrument ends recording"):str,
                        Optional("aliases"):Or(str, list)
                    }
                }
            },
            "channel":{
                "schema":{
                    "_id":{
                        "type":"ObjectID",
                        Optional("concept", default="ObjectId used to define a particular component of data"):str,
                    },
                    "net":{
                        "reference":"site"
                    },
                    "sta":{
                        "reference":"site"
                    },
                    Optional("loc"):{
                        "type":"string",
                        Optional("concept", default="location code assigned to an instrument (loc component of SEED net:sta:chan)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "chan":{
                        "type":"string",
                        Optional("concept", default="channel name (e.g. HHZ, BHE, etc.) - normally a SEED channel code"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "lat":{
                        "type":"double",
                        Optional("concept", default="latitude of a seismic station/instrument in degrees"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "lon":{
                        "type":"double",
                        Optional("concept", default="longitude of a seismic station/instrument in degrees"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "elev":{
                        "type":"double",
                        Optional("concept", default="elevation of a seismic station/instrument in km (subtract emplacement depth for borehole instruments)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "edepth":{
                        "type":"double",
                        Optional("concept", default="depth of a seismic station/instrument in km"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "hang":{
                        "type":"double",
                        Optional("concept", default="Azimuth (in degree) of a seismometer component - horizontal angle"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "vang":{
                        "type":"double",
                        Optional("concept", default="Inclination from +up (in degree) of a seismometer component - vertical angle"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "starttime":{
                        "type":"double",
                        Optional("concept", default="Time of seismic channel starts recording"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "endtime":{
                        "type":"double",
                        Optional("concept", default="Time of seismic channel ends recording"):str,
                        Optional("aliases"):Or(str, list)
                    }
                }
            },
            "source":{
                "schema":{
                    "_id":{
                        "type":"ObjectID",
                        Optional("concept", default="ObjectId used to define a particular seismic source"):str,
                    },
                    "lat":{
                        "type":"double",
                        Optional("concept", default="Latitude (in degrees) of the hypocenter of seismic source"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "lon":{
                        "type":"double",
                        Optional("concept", default="Longitude (in degrees) of the hypocenter of seismic source"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "depth":{
                        "type":"double",
                        Optional("concept", default="Depth (in km) of the hypocenter of seismic source"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "time":{
                        "type":"double",
                        Optional("concept", default="Origin time of the hypocenter of seismic source (epoch time)"):str,
                        Optional("aliases"):Or(str, list)
                    },
                    "magnitude":{
                        "type":"double",
                        Optional("concept", default="Generic magnitude attribute"):str,
                        Optional("aliases"):Or(str, list)
                    },
                }
            },
            "history_object":{
                "schema":{
                    "_id":{
                        "type":"string",
                        Optional("concept", default="UUID used to define an unique entry in history collection."):str
                    },
                    "nodedata":{
                        "type":"bytes",
                        Optional("concept", default="serialized content of ProcessingHistory"):str
                    }
                }
            },
            Optional("elog"):{
                "schema":{
                    "_id":{
                        "type":"ObjectID",
                        Optional("concept", default="ObjectID used to define an unique entry in elog collection."):str
                    },
                    "logdata":{
                        "type":"list",
                        Optional("concept", default="a list of LogData."):str
                    },
                    Optional("wf_Seismogram_id"):{
                        "reference":"wf_Seismogram"
                    },
                    Optional("wf_TimeSeries_id"):{
                        "reference":"wf_TimeSeries"
                    },
                    Optional("gravestone"):{
                        "type":"dict",
                        Optional("concept", default="a copy of the Metadata of a dead object."):str
                    }
                }
            }
        },
        "Metadata":{
            "TimeSeries":{
                "schema":{
                    "_id":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="true"):bool
                    },
                    "npts":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "delta":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "sampling_rate":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "starttime":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "time_standard":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    Optional("calib"):{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "site_id":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "channel_id":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "source_id":{
                        "collection":"wf_TimeSeries",
                        Optional("readonly", default="false"):bool
                    },
                    "net":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "sta":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_lat":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_lon":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_elev":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_starttime":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_endtime":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "loc":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "chan":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_hang":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_vang":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_lat":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_lon":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_elev":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_edepth":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_starttime":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "channel_endtime":{
                        "collection":"channel",
                        Optional("readonly", default="true"):bool
                    },
                    "source_lat":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_lon":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_depth":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_time":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_magnitude":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                }
            },
            "Seismogram":{
                "schema":{
                    "_id":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="true"):bool
                    },
                    "npts":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "delta":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "sampling_rate":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "starttime":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "time_standard":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    Optional("calib"):{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "site_id":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "channel_id":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "source_id":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "tmatrix":{
                        "collection":"wf_Seismogram",
                        Optional("readonly", default="false"):bool
                    },
                    "net":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "sta":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "loc":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_lat":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_lon":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_elev":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_starttime":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "site_endtime":{
                        "collection":"site",
                        Optional("readonly", default="true"):bool
                    },
                    "source_lat":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_lon":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_depth":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_time":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                    "source_magnitude":{
                        "collection":"source",
                        Optional("readonly", default="true"):bool
                    },
                }
            }
        },
        Optional("Other"):{
            "schema":dict
        }
    }
    
    Schema(schema, ignore_extra_keys=True).validate(schema_dic)