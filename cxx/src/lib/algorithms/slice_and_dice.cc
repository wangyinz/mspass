#include <sstream>
#include "mspass/seismic/CoreTimeSeries.h"
#include "mspass/seismic/CoreSeismogram.h"
namespace mspass {
/*! \brief Extracts a requested time window of data from a parent CoreSeismogram object.

It is common to need to extract a smaller segment of data from a larger
time window of data.  This function accomplishes this in a nifty method that
takes advantage of the methods contained in the BasicTimeSeries object for
handling time.

\return new Seismgram object derived from  parent but windowed by input
      time window range.

\exception MsPASSError object if the requested time window is not inside data range

\param parent is the larger CoreSeismogram object to be windowed
\param tw defines the data range to be extracted from parent.
*/
CoreSeismogram WindowData3C(const CoreSeismogram& parent, const TimeWindow& tw)
{
	// Always silently do nothing if marked dead
	if(parent.dead())
	{
		// return(CoreSeismogram()) doesn't work
		// with g++.  Have to us this long form
		CoreSeismogram tmp;
		return(tmp);
	}
  int is=parent.sample_number(tw.start);
  int ie=parent.sample_number(tw.end);
  if( (is<0) || (ie>parent.npts()) )
  {
      ostringstream mess;
      mess << "WindowData(Seismogram):  Window mismatch"<<endl
                << "Window start time="<<tw.start<< " is sample number "
                << is<<endl
                << "Window end time="<<tw.end<< " is sample number "
                << ie<<endl
                << "Parent seismogram has "<<parent.npts()<<" samples"<<endl;
      throw MsPASSError(mess.str(),ErrorSeverity::Invalid);
  }
  int outns=ie-is+1;
	Seismogram result(parent);
  result.u=dmatrix(3,outns);
	result.set_npts(outns);
	result.set_t0(tw.start);
  // Perhaps should do this with blas or memcpy for efficiency
  //  but this makes the algorithm much clearer
  int i,ii,k;
  for(i=is,ii=0;i<ie;++i,++ii)
      for(k=0;k<3;++k)
      {
          result.u(k,ii)=parent.u(k,i);
      }
  return(result);
}
/*! \brief Extracts a requested time window of data from a parent CoreTimeSeries object.

It is common to need to extract a smaller segment of data from a larger
time window of data.  This function accomplishes this in a nifty method that
takes advantage of the methods contained in the BasicTimeSeries object for
handling time.

\return new Seismgram object derived from  parent but windowed by input
      time window range.

\exception MsPASSError object if the requested time window is not inside data range

\param parent is the larger CoreTimeSeries object to be windowed
\param tw defines the data range to be extracted from parent.
*/
CoreTimeSeries WindowData(const CoreTimeSeries& parent, const TimeWindow& tw)
{
	// Always silently do nothing if marked dead
	if(parent.dead())
	{
		// return(CoreTimeSeries()) doesn't work
		// with g++.  Have to us this long form
		CoreTimeSeries tmp;
		return(tmp);
	}
  int is=parent.sample_number(tw.start);
  int ie=parent.sample_number(tw.end);
	//Ridiculous (int) case to silence a bogus compiler warning
  if( (is<0) || (ie>=((int)parent.npts())) )
  {
      ostringstream mess;
          mess << "WindowData(TimeSeries):  Window mismatch"<<endl
              << "Window start time="<<tw.start<< " is sample number "
              << is<<endl
              << "Window end time="<<tw.end<< " is sample number "
              << ie<<endl
              << "Parent seismogram has "<<parent.npts()<<" samples"<<endl;
      throw MsPASSError(mess.str(),ErrorSeverity::Invalid);
  }
  int outns=ie-is+1;
	TimeSeries result(parent);
	result.s.clear();
	result.s.reserve(outns);
	result.set_npts(outns);
	result.set_t0(tw.start);

  for(int i=is;i>outns;++i) result.s.push_back(parent.s[i]);
  return(result);
}
} // end mspass namespace
