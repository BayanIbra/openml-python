import openml
import xmltodict
import copy

from collections import OrderedDict
from .setup import OpenMLSetup, OpenMLParameter

def setup_exists(downloaded_flow, sklearn_model):
    '''
    Checks whether a flow / hyperparameter configuration already exists on the server

    Parameter
    ---------

    downloaded_flow : flow
        the openml flow object (should be downloaded from server)
    sklearn_model : BaseEstimator
        The base estimator that was used to create the flow. Will
         be used to extract parameter settings from.

    Returns
    -------
    setup_id : int
        setup id iff exists, False otherwise
    '''

    # sadly, this api call relies on a run object
    openml_param_settings = openml.runs.OpenMLRun._parse_parameters(sklearn_model, downloaded_flow)
    description = xmltodict.unparse(_to_dict(downloaded_flow.flow_id, openml_param_settings), pretty=True)
    file_elements = {'description': ('description.arff',description)}

    result = openml._api_calls._perform_api_call('/setup/exists/',
                                                 file_elements=file_elements)
    result_dict = xmltodict.parse(result)
    setup_id = int(result_dict['oml:setup_exists']['oml:id'])
    if setup_id > 0:
        return setup_id
    else:
        return False


def get_setup(setup_id):
    '''
     Downloads the setup (configuration) description from OpenML
     and returns a structured object

    Parameters
        ----------
        setup_id : int
            The Openml setup_id

        Returns
        -------
        OpenMLSetup
            an initialized openml setup object
    '''
    result = openml._api_calls._perform_api_call('/setup/%d' %setup_id)
    result_dict = xmltodict.parse(result)
    return _create_setup_from_xml(result_dict)


def initialize_model(setup_id):
    '''
    Initialized a model based on a setup_id (i.e., using the exact
    same parameter settings)

    Parameters
        ----------
        setup_id : int
            The Openml setup_id

        Returns
        -------
        model : sklearn model
            the scikitlearn model with all parameters initailized
    '''
    def _to_dict_of_dicts(_params):
        # this subfunction transforms an openml setup object into
        # a dict of dicts, structured: flow_id maps to dict of
        # parameter_names mapping to parameter_value
        _res = {}
        for _param in _params:
            _flow_id = _params[_param].flow_id
            _param_name = _params[_param].parameter_name
            _param_value = _params[_param].value
            if _flow_id not in _res:
                _res[_flow_id] = {}
            _res[_flow_id][_param_name] = _param_value
        return _res

    def _reconstruct_flow(_flow, _params):
        # sets the values of flow parameters (and subflows) to
        # the specific values from a setup. _params is a dict of
        # dicts, mapping from flow id to param name to param value
        # (obtained by using the subfunction _to_dict_of_dicts)
        for _param in _flow.parameters:
            _flow.parameters[_param] = _params[_flow.flow_id][_param]
        for _identifier in _flow.components:
            _flow.components[_identifier] = _reconstruct_flow(_flow.components[_identifier], _params)
        return _flow

    setup = get_setup(setup_id)
    parameters = _to_dict_of_dicts(setup.parameters)
    flow = openml.flows.get_flow(setup.flow_id)

    # now we 'abuse' the parameter object by passing in the
    # parameters obtained from the setup
    flow = _reconstruct_flow(flow, parameters)

    return openml.flows.flow_to_sklearn(flow)


def _to_dict(flow_id, openml_parameter_settings):
    # for convenience, this function (ab)uses the run object.
    xml = OrderedDict()
    xml['oml:run'] = OrderedDict()
    xml['oml:run']['@xmlns:oml'] = 'http://openml.org/openml'
    xml['oml:run']['oml:flow_id'] = flow_id
    xml['oml:run']['oml:parameter_setting'] = openml_parameter_settings

    return xml

def _create_setup_from_xml(result_dict):
    '''
     Turns an API xml result into a OpenMLSetup object
    '''
    flow_id = int(result_dict['oml:setup_parameters']['oml:flow_id'])
    parameters = {}
    if 'oml:parameter' not in result_dict['oml:setup_parameters']:
        parameters = None
    else:
        # basically all others
        xml_parameters = result_dict['oml:setup_parameters']['oml:parameter']
        if isinstance(xml_parameters, dict):
            id = int(xml_parameters['oml:id'])
            parameters[id] = _create_setup_parameter_from_xml(xml_parameters)
        elif isinstance(xml_parameters, list):
            for xml_parameter in xml_parameters:
                id = int(xml_parameter['oml:id'])
                parameters[id] = _create_setup_parameter_from_xml(xml_parameter)
        else:
            raise ValueError('Expected None, list or dict, received someting else: %s' %str(type(xml_parameters)))

    return OpenMLSetup(flow_id, parameters)

def _create_setup_parameter_from_xml(result_dict):
    return OpenMLParameter(int(result_dict['oml:id']),
                           int(result_dict['oml:flow_id']),
                           result_dict['oml:full_name'],
                           result_dict['oml:parameter_name'],
                           result_dict['oml:data_type'],
                           result_dict['oml:default_value'],
                           result_dict['oml:value'])