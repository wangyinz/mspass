#ifndef _MSPASS_CORESEISMOGRAM_H_
#define _MSPASS_CORESEISMOGRAM_H_
#include <memory>
#include <vector>
#include "mspass/utility/Metadata.h"
#include "mspass/utility/dmatrix.h"
#include "mspass/seismic/BasicTimeSeries.h"
#include "mspass/seismic/CoreTimeSeries.h"
#include "mspass/utility/SphericalCoordinate.h"
#include "mspass/seismic/SlownessVector.h"
#include "mspass/seismic/TimeWindow.h"
#include "mspass/seismic/Ensemble.h"
namespace mspass{

/* A Seismogram is viewed as a special collection of Time Series
type data that is essentially a special version of a vector time series.
It is "special" as the vector is 3D with real components.  One could produce a
similar inherited type for an n vector time series object.

The structure of a vector time series allows the data to be stored in a matrix.
Here we use a lightweight matrix object I call dmatrix.   This object is
contains core concepts that define a seismogram.   It can be extended as in
MsPASS to add functionality or aliased to Seismogram to simplify the naming as
done, for example, with std::basic_string made equivalent to std::string.
*/


/*! \brief Vector (three-component) seismogram data object.

 A three-component seismogram is a common concept in seismology. The concept
 used here is that a three-component seismogram is a time series with a 3-vector
 as the data at each time step.  As a result the data are stored internally as
 a matrix with row defining the component number (C indexing 0,1,2) and
 the column defining the time variable.
 The object inherits common concepts of a time series through the
 BasicTimeSeries object.  Auxiliary parameters are defined for the object
 through inheritance of a Metadata object.
\author Gary L. Pavlis
**/
class CoreSeismogram : public mspass::BasicTimeSeries , public mspass::Metadata
{
public:
 /*!
 Holds the actual data.

Matrix is 3xns.  Thus the rows are the component number
 and columns define time position.  Note there is a redundancy in
 these definitions that must be watched if you manipulate the
 contents of this matrix.  That is, BasicTimeSeries defines ns, but
 the u matrix has it's own internal size definitions.  Currently no
 tests are done to validate this consistency.  All constructors handle
 this, but again because u is public be very careful in altering u.
**/
	dmatrix u;

/*!
 Default constructor.

Sets ns to zero and builds an empty data matrix.  The live variable
in BasicTimeSeries is also set false.
**/
	CoreSeismogram();
/*!
 Simplest parameterized constructor.

Initializes data and sets aside memory for
 matrix of size 3xnsamples.  The data matrix is not initialized
 and the object is marked as not live.
\param nsamples number of samples expected for holding data.
**/
	CoreSeismogram(const int nsamples);
/*!
 Construct a three component seismogram from three TimeSeries objects.

 A three component seismogram is commonly assembled from individual
 single channel components.  This constructor does the process taking
 reasonable care to deal with (potentially) irregular start and end
 times of the individual components.  If the start and end times are
 all the same it uses a simple copy operation.  Otherwise it runs a
 more complicated  (read much slower) algorithm that handles the ragged
 start and stop times by adding a marked gap.  That is, the object is
 allocated with space for the earliest start and last end time.  Areas
 at front and back with one or two channels missing are marked as a
 gap.

 This constructor handles gaps in the three components correctly as the
 union of the gaps found in all three.  The current algorithm for doing
 this is slow but running a sample by sample test on each component and
 marking gaps with the BasicTimeSeries add_gap methods.

 Note this constructor requires variables hang and vang, which are
 orientation angles defined in the CSS3.0 schema (NOT spherical
 coordinates by the way), by set for each component.  This is used to
 construct the transformation matrix for the object that allows,
 for example, removing raw data orientation errors using rotate_to_standard.
 The constructor will throw an exception if any component does not have
 these attributes set in their Metadata area.

\exception SeisppError exception can be throw for a variety of serious
    problems.
\param ts vector of 3 TimeSeries objects to be used to assemble
  this Seismogram.  Input vector order could be
  arbitrary because a transformation matrix is computed, but for
  efficiency standard order (E,N,Z) is advised.
\param component_to_clone the auxiliary parameters (Metadata and
   BasicTimeSeries common parameters)
   from one of the components is cloned to assure common required
   parameters are copied to this object.  This argument controls which
   of the three components passed through ts is used.  Default is 0.

**/
	CoreSeismogram(const vector<mspass::CoreTimeSeries>& ts,
		const int component_to_clone=0);
/*! \brief Construct from Metadata definition that includes data path.
 *
 A Metadata object is sufficiently general that it can contain enough
 information to contruct an object from attributes contained in it. 
 This constuctor uses that approach, with the actual loading of data 
 being an option (on by default).   In mspass this is constructor is
 used to load data with Metadata constructed from MongoDB and then 
 using the path created from two parameters (dir and dfile used as
 in css3.0 wfdisc) to read data.   The API is general but the 
 implementation in mspass is very rigid.   It blindly assumes the
 data being read are binary doubles in the right byte order and 
 ordered in the native order for dmatrix (Fortran order).  i.e.
 the constuctor does a raw fread of ns*3 doubles into the internal
 array used in the dmatrix implementation. 

 \param md is the Metadata used for the construction.  It MUST contain
 all of the following or it will fail:  delta, starttime,npts,U11,U21,
 U31,U21,U22,U23,U31,U32,U33,dir,dfile, and foff.  

 \param load_data if true (default) a file name is constructed from 
 dir+"/"+dfile, the file is openned, fseek is called to foff, 
 data are read with fread, and the file is closed.  If false a dmatrix
 for u is still created of size 3xns, but the matrix is only initialized
 to all zeros.  

 \exception  Will throw a MsPASSError if required metadata are missing.
 */
        CoreSeismogram(const mspass::Metadata& md,const bool load_data=true);
/*!
 Standard copy constructor.
**/

	CoreSeismogram(const CoreSeismogram&);
/*!
 Standard assignment operator.
**/
	CoreSeismogram& operator
		= (const CoreSeismogram&);
/*!
 Extract a sample from data vector.

 A sample in this context means a three-vector at a requested
 sample index.  Range checking is implicit because
 of the internal use of the dmatrix to store the samples of
 data.  This operator is an alternative to extracting samples
 through indexing of the internal dmatrix u that holds the data.

\param sample is the sample number requested (must be in range or an exception will be thrown)

\exception MsPASSError if the requested sample is outside
    the range of the data.  Note this includes an implicit "outside"
    defined when the contents are marked dead.
    Note the code does this by catching an error thrown by dmatrix
    in this situation, printing the error message from the dmatrix
    object, and then throwing a new SeisppError with a shorter
    message.
\return std::vector containing a 3 vector of the samples at requested sample number

\param sample is the integer sample number of data desired.
**/
        std::vector<double> operator[](const int sample)const;
/*! \brief Overloaded version of operator[] for time.

Sometimes it is useful to ask for data at a specified time without worrying
about the time conversion.   This simplifies that process.  It is still subject
to an exception if the the time requested is outside the data range.

\param time  is the time of the requested sample
\return 3 vector of data samples at requested time
\exception MsPASSError will be thrown if the time is outside the data range.

*/
        std::vector<double> operator[](const double time)const;
/*! Standard destructor. */
	~CoreSeismogram(){};
/*!
 Apply inverse transformation matrix to return data to cardinal direction components.

 It is frequently necessary to make certain a set of three component data are oriented
 to the standard reference frame (EW, NS, Vertical).  This function does this.
 For efficiency it checks the components_are_cardinal variable and does nothing if
 it is set true.  Otherwise, it applies the inverse transformation and then sets this variable true.
 Note even if the current transformation matrix is not orthogonal it will be put back into
 cardinal coordinates.
 \exception SeisppError thrown if the an inversion of the transformation matrix is required and that
 matrix is singular.  This can happen if the transformation matrix is incorrectly defined or the
 actual data are coplanar.
**/
	void rotate_to_standard();
	// This overloaded pair do the same thing for a vector
	// specified as a unit vector nu or as spherical coordinate angles
/*!
 Rotate data using a P wave type coordinate definition.

 In seismology the longitudinal motion direction of a P wave defines a direction
 in space.  This method rotates the data into a coordinate system defined by a
 direction passed through the argument.  The data are rotated such that x1 becomes
 the transverse component, x2 becomes radial, and x3 becomes longitudinal.  In the
 special case for a vector pointing in the x3 direction the data are not altered.
 The transformation matrix is effectively the matrix product of two coordinate rotations:
 (1) rotation around x3 by angle phi and (2) rotation around x1 by theta.

The sense of this transformation is confusing because of a difference in
convention between spherical coordinates and standard earth coordinates.
In particular, orientation on the earth uses a convention with x2 being
the x2 axis and bearings are relative to that with a standard azimuth
measured clockwise from north.  Spherical coordinate angle phi (used here)
is measured counterclockwise relative to the x1 axis, which is east in
standard earth coordinates. This transformation is computed using a phi
angle.   To use this then to compute a transformation to standard ray
coordinates with x2 pointing in the direction of wavefront advance,
phi should be set to pi/2-azimuth which gives the phi angle needed to rotate
x2 to radial.  This is extremely confusing because in spherical coordinates
it would be more intuitive to rotate x1 to radial, but this is NOT the
convention used here.  In general to use this feature the best way to avoid
this confusion is to use the PMHalfSpaceModel procedure to compute a
SphericalCoordinate object consistent with given propagation direction
defined by a slowness vector.  Alternatively, use the free_surface_transformation
method defined below.

A VERY IMPORTANT thing to recognize about this tranformation is it will
always yield a result relative to cardinal coordinates.  i.e. if the data
had been previously rotated or were not originally in ENZ form they
will be first transformed to ENZ before actually performing this
transformation.   Use the transform or horizontal rotation method to
create cummulative transformations.

\param sc defines final x3 direction (longitudinal) in a spherical coordinate structure.
**/
	void rotate(SphericalCoordinate& sc);

/*!
 Rotate data using a P wave type coordinate definition.

 In seismology the longitudinal motion direction of a P wave defines a direction
 in space.  This method rotates the data into a coordinate system defined by a
 direction passed through the argument.  The data are rotated such that x1 becomes
 the transverse component, x2 becomes radial, and x3 becomes longitudinal.  In the
 special case for a vector pointing in the x3 direction the data are not altered.

 This method effectively turns nu into a SphericalCoordinate object and calles the
 related rotate method that has a SphericalCoordinate object as an argument.  The
 potential confusion of orientation is not as extreme here.  After the transformation
 x3prime will point in the direction of nu, x2 will be in the x3-x3prime plane (rotation by
 theta) and orthogonal to x3prime, and x1 will be horizontal and perpendicular to x2prime
 and x3prime.

A VERY IMPORTANT thing to recognize about this tranformation is it will
always yield a result relative to cardinal coordinates.  i.e. if the data
had been previously rotated or were not originally in ENZ form they
will be first transformed to ENZ before actually performing this
transformation.   Use the transform or horizontal rotation method to

\param nu defines direction of x3 direction (longitudinal) as a unit vector with three components.
**/
	void rotate(const double nu[3]);
  /*! \brief Rotate horizontals by a simple angle in degrees.

          A common transformation in 3C processing is a rotation of the
          horizontal components by an angle.  This leaves the vertical
          (assumed here x3) unaltered.   This routine rotates the horizontals
          by angle phi using with positive phi counterclockwise as in
          polar coordinates and the azimuth angle of spherical coordinates.

          Note this transformation is cummulative.  i.e. this transformation
          is cumulative.  The internal transformation matrix will be updated.
          This is a useful feature for things like incremental horizontal
          rotation in rotational angle grid searches.

          \param phi rotation angle around x3 axis in counterclockwise
            direction (in radians).
    */
  void rotate(const double phi);
/*!
 Applies an arbitrary transformation matrix to the data.
 i.e. after calling this method the data will have been multiplied by the matrix a
 and the transformation matrix will be updated.  The later allows cascaded
 transformations to data.

\param a is a C style 3x3 matrix.
**/
	void transform(const double a[3][3]);
/*!
 Computes and applies the Kennett [1991] free surface transformation matrix.

 Kennett [1991] gives the form for a free surface transformation operator
 that reduces to a nonorthogonal transformation matrix when the wavefield is
 not evanescent.  On output x1 will be transverse, x2 will be SV (radial),
 and x3 will be longitudinal.

\param u slowness vector off the incident wavefield
\param vp0 Surface P wave velocity
\param vs0 Surface S wave velocity.
**/
	void free_surface_transformation(const mspass::SlownessVector u, const double vp0, const double vs0);
/*! Return current transformation matrix.

The transformation matrix is maintained internally in this object.
Transformations like rotations and the transform method can change make
this matrix not an identity matrix.  It should always be an identity
matrix when the coordinates are cardinal (i.e. ENZ).

\return 3x3 transformation matrix.
*/
        dmatrix get_transformation_matrix()
        {
            dmatrix result(3,3);
            for(int i=0;i<3;++i)
                for(int j=0;j<3;++j) result(i,j)=tmatrix[i][j];
            return result;
        };
/*! \brief Define the transformaton matrix.
 *
 Occasionally we need to set the transformation matrix manually.
 The type example is input with a format where the component 
 directions are embedded.  We use a dmatrix as it is more 
 easily wrapped for python than the raw C 2D array which 
 really doesn't translate well between the languages.   

 \param A is the 3X3 matrix copied to the internal transformation
   matrix array.
 
 \return true if the given transformation matrix is an identity
   meaning components_are_cardinal gets set true. 
   false if the test for an identity matrix fails. 
 \exception Will throw a MsPASSError if the input matrix is
   not 3x3.
   */
        bool set_transformation_matrix(const dmatrix& A);

protected:
	/*!
	 Defines if the contents of this object are components of an orthogonal basis.

	 Most raw 3c seismic data use orthogonal components, but this is not universal.
	 Furthermore, some transformations (e.g. the free surface transformation operator)
	 define transformations to basis sets that are not orthogonal.  Because
	 detecting orthogonality from a transformation is a nontrivial thing
	 (rounding error is the complication) this is made a part of the object to
	 simplify a number of algorithms.
	**/
		bool components_are_orthogonal;
	/*!
	 Defines of the contents of the object are in Earth cardinal coordinates.

	 Cardinal means the cardinal directions at a point on the earth.  That is,
	 x1 is positive east, x2 is positive north, and x3 is positive up.
	 Like the components_are_orthogonal variable the purpose of this variable is
	 to simplify common tests for properties of a given data series.
	**/
		bool components_are_cardinal;  // true if x1=e, x2=n, x3=up
	/*!
	 Transformation matrix.

	 This is a 3x3 transformation that defines how the data in this object is
	 produced from cardinal coordinates.  That is, if u is the contents of this
	 object the data in cardinal directions can be produced by tmatrix^-1 * u.
	**/
		double tmatrix[3][3];
private:
  /* This is used internally when necessary to test if a computed or input
           matrix is an identity matrix. */
  bool tmatrix_is_cardinal();
};
//
////////////////////////////////////////////////////
//  Start helper function prototypes
///////////////////////////////////////////////////
//
/*! \brief Return a new CoreSeismogram in an arrival time (relative) refernce frame.

 An arrival time reference means that the time is set to relative and
 zero is defined as an arrival time extracted from the metadata area of
 the object.  The key used to extract the arrival time used for the
 conversion is passed as a variable as this requires some flexibility.
 To preserve the absolute time standard in this conversion the 0 time
 computed from the arrival time field is used to compute the absolute
 time of the start of the output seismogram as atime+t0.  This result
 is stored in the metadata field keyed by the word "time".  This allows
 one to convert the data back to an absolute time standard if they so
 desire, but it is less flexible than the input key method.

\exception SeisppError for errors in extracting required information from metadata area.

\param din  is input seismogram
\param key is the metadata key used to find the arrival time to use as a reference.
\param tw is a TimeWindow object that defines the window of data to extract around
    the desired arrival time.
**/
std::shared_ptr<CoreSeismogram> ArrivalTimeReference(CoreSeismogram& din,
	std::string key, mspass::TimeWindow tw);
/*!
 Extract one component from a Seismogram and
 create a CoreTimeSeries object from it.

\param tcs is the Seismogram to convert.
\param component is the component to extract (0, 1, or 2)
\param mdl list of metadata to copy to output from input object.
**/
std::shared_ptr<mspass::CoreTimeSeries> ExtractComponent(CoreSeismogram& tcs,int component,
        mspass::MetadataList& mdl);
/*!
 Extract one component from a CoreSeismogram and
 create a CoreTimeSeries object from it.

 Similar to overloaded function of same name, but all metadata from
 parent is copied to the output.

\param tcs is the CoreSeismogram to convert.
\param component is the component to extract (0, 1, or 2)
**/
std::shared_ptr<mspass::CoreTimeSeries> ExtractComponent(CoreSeismogram& tcs,int component);
}  //end mspass namespace enscapsulation
#endif  // End guard
