import numpy as np
import mspasspy.ccore as mspass
from mspasspy.ccore import Seismogram, TimeSeries, TimeSeriesEnsemble, SeismogramEnsemble, MsPASSError


def info(data, algname, instance, target=None):
    """
    This helper function is used to log operations in processing history of mspass object.
    Per best practice, every operations happen on the mspass object should be logged.
    :param data: the mspass data object
    :param algname: the name of the algorithm that used on the mspass object.
    :param instance: an id designator to uniquely define an instance of algorithm.
    :param target: if the mspass data object is an ensemble type, you may use target as index to
    log on one specific object in the ensemble. If target is not specified, all the objects in the ensemble
    will be logged using the same information.
    :return: None
    """
    empty_err_message = "cannot preserve history because container was empty\n" + \
                        "Must at least contain an origin record"

    if isinstance(data, (mspass.TimeSeries, mspass.Seismogram)):
        if data.live:
            if data.is_empty():
                data.elog.log_error(algname, empty_err_message, mspass.ErrorSeverity.Complaint)
            else:
                data.new_map(algname, instance,
                             mspass.AtomicType.TIMESERIES if isinstance(data,
                                                                        mspass.TimeSeries) else mspass.AtomicType.SEISMOGRAM,
                             mspass.ProcessingStatus.VOLATILE)

    elif isinstance(data, (mspass.TimeSeriesEnsemble, mspass.SeismogramEnsemble)):
        if (target is not None) and (len(data.member) <= target):
            raise IndexError("logging_helper.info: target index is out of bound")
        for i in range(len(data.member)) if target is None else [target]:
            if data.member[i].live:  # guarantee group member is not dead
                if data.member[i].is_empty():
                    data.member[i].elog.log_error(algname, empty_err_message, mspass.ErrorSeverity.Complaint)
                else:
                    data.member[i].new_map(algname, instance,
                                           mspass.AtomicType.TIMESERIES \
                                               if isinstance(data.member[i],
                                                             mspass.TimeSeries) else mspass.AtomicType.SEISMOGRAM,
                                           mspass.ProcessingStatus.VOLATILE)
    else:
        print('Coding error - logging.info was passed an unexpected data type of', type(data))
        print('Not treated as fatal but a bug fix is needed')


def ensemble_error(d, alg, message, err_severity=mspass.ErrorSeverity.Invalid):
    """
    This is a small helper function useful for error handlers in except 
    blocks for ensemble objects.  If a function is called on an ensemble 
    object that throws an exception this function will post the message 
    posted to all ensemble members.  It silently does nothing if the 
    ensemble is empty. 
    :param err_severity: severity of the error, default as mspass.ErrorSeverity.Invalid.
    :param d: is the ensemble data to be handled. It print and error message
      and returns doing nothing if d is not one of the known ensemble 
      objects.
    :param alg: is the algorithm name posted to elog on each member
    :param message: is the string posted to all members
    (Note due to a current flaw in the api we don't have access to the 
    severity attribute.  For now this always set it Invalid)
    """
    if isinstance(d, (mspass.TimeSeriesEnsemble, mspass.SeismogramEnsemble)):
        n = len(d.member)
        if n <= 0:
            return
        for i in range(n):
            d.member[i].elog.log_error(alg, str(message), err_severity)
    else:
        print('Coding error - ensemble_error was passed an unexpected data type of',
              type(d))
        print('Not treated as fatal but a bug fix is needed')


def reduce(data1, data2, algname, instance):
    """
    This function replicates the processing history of data2 onto data1, which is a common use case
    in reduce stage. If data1 is dead, it will keep silent, i.e. no history will be replicated. If data2 is dead,
    the processing history will still be replicated.
    :param data1: Mspass object
    :param data2: Mspass object
    :param algname: The name of the reduce algorithm that uses this helper function.
    :param instance: The unique id of that user gives to the algorithm.
    :return: None
    """
    if isinstance(data1, (mspass.TimeSeries, mspass.Seismogram)):
        if type(data1) != type(data2):
            raise TypeError("logging_helper.reduce: data2 has a different type as data1")
        if data1.live:
            data1.accumulate(algname,
                             instance,
                             mspass.AtomicType.TIMESERIES if isinstance(data1,mspass.TimeSeries)
                                else mspass.AtomicType.SEISMOGRAM,
                             data2)

    elif isinstance(data1, (mspass.TimeSeriesEnsemble, mspass.SeismogramEnsemble)):
        if type(data1) != type(data2):
            raise TypeError("logging_helper.reduce: data2 has a different type as data1")
        if len(data1.member) != len(data2.member):
            raise IndexError("logging_helper.reduce: data1 and data2 have different sizes of member")
        for i in range(len(data1.member)):
            if data1.member[i].live:  # guarantee group member is not dead
                data1.member[i].accumulate(algname,
                                 instance,
                                 mspass.AtomicType.TIMESERIES if isinstance(data1.member[i], mspass.TimeSeries)
                                    else mspass.AtomicType.SEISMOGRAM,
                                 data2.member[i])
    else:
        print('Coding error - logging.reduce was passed an unexpected data type of', type(data1))
        print('Not treated as fatal but a bug fix is needed')
